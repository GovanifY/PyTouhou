use image::GenericImageView;
use luminance::context::GraphicsContext;
use luminance::framebuffer::Framebuffer;
use luminance::pipeline::BoundTexture;
use luminance::pixel::{NormRGB8UI, Floating};
use luminance::render_state::RenderState;
use luminance::shader::program::{Program, Uniform};
use luminance::tess::{Mode, TessBuilder};
use luminance::texture::{Dim2, Flat, Sampler, Texture, GenMipmaps};
use luminance_derive::{Semantics, Vertex, UniformInterface};
use luminance_glfw::event::{Action, Key, WindowEvent};
use luminance_glfw::surface::{GlfwSurface, Surface, WindowDim, WindowOpt};
use touhou::th06::anm0::Anm0;
use touhou::th06::anm0_vm::{Sprite, Vertex as FakeVertex};
use touhou::th06::ecl::{Ecl, Rank};
use touhou::th06::ecl_vm::EclRunner;
use touhou::th06::enemy::{Enemy, Game, Position};
use touhou::util::math::{perspective, setup_camera};
use touhou::util::prng::Prng;
use std::cell::RefCell;
use std::fs::File;
use std::io::{BufReader, Read};
use std::rc::Rc;
use std::env;
use std::path::Path;

const VS: &str = r#"
in ivec3 in_position;
in vec2 in_texcoord;
in uvec4 in_color;

uniform mat4 mvp;

out vec2 texcoord;
out vec4 color;

void main()
{
    gl_Position = mvp * vec4(vec3(in_position), 1.0);
    texcoord = vec2(in_texcoord);

    // Normalized from the u8 being passed.
    color = vec4(in_color) / 255.;
}
"#;

const FS: &str = r#"
in vec2 texcoord;
in vec4 color;

uniform sampler2D color_map;

out vec4 frag_color;

void main()
{
    frag_color = texture(color_map, texcoord) * color;
}
"#;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Semantics)]
pub enum Semantics {
    #[sem(name = "in_position", repr = "[i16; 3]", wrapper = "VertexPosition")]
    Position,

    #[sem(name = "in_texcoord", repr = "[f32; 2]", wrapper = "VertexTexcoord")]
    Texcoord,

    #[sem(name = "in_color", repr = "[u8; 4]", wrapper = "VertexColor")]
    Color,
}

#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Vertex)]
#[vertex(sem = "Semantics")]
struct Vertex {
    pos: VertexPosition,
    uv: VertexTexcoord,
    rgba: VertexColor,
}

#[derive(UniformInterface)]
struct ShaderInterface {
    // the 'static lifetime acts as “anything” here
    color_map: Uniform<&'static BoundTexture<'static, Flat, Dim2, Floating>>,

    #[uniform(name = "mvp")]
    mvp: Uniform<[[f32; 4]; 4]>,
}

fn main() {
    // Parse arguments.
    let args: Vec<_> = env::args().collect();
    if args.len() != 6 {
        eprintln!("Usage: {} <ECL file> <ANM file> <PNG file> <easy|normal|hard|lunatic> <sub number>", args[0]);
        return;
    }
    let ecl_filename = &args[1];
    let anm_filename = &args[2];
    let png_filename = &args[3];
    let rank: Rank = args[4].parse().expect("rank");
    let sub: u8 = args[5].parse().expect("number");

    // Open the ECL file.
    let file = File::open(ecl_filename).unwrap();
    let mut file = BufReader::new(file);
    let mut buf = vec![];
    file.read_to_end(&mut buf).unwrap();
    let (_, ecl) = Ecl::from_slice(&buf).unwrap();

    // Open the ANM file.
    let file = File::open(anm_filename).unwrap();
    let mut file = BufReader::new(file);
    let mut buf = vec![];
    file.read_to_end(&mut buf).unwrap();
    let anm0 = Anm0::from_slice(&buf).unwrap();
    let anm0 = Rc::new(RefCell::new(anm0));

    if ecl.subs.len() < sub as usize {
        eprintln!("This ecl doesn’t contain a sub named {}.", sub);
        return;
    }

    // TODO: seed this PRNG with a valid seed.
    let prng = Rc::new(RefCell::new(Prng::new(0)));

    // Create the Game god object.
    let game = Game::new(prng, rank);
    let game = Rc::new(RefCell::new(game));

    // And the enemy object.
    let enemy = Enemy::new(Position::new(0., 0.), 500, 0, 640, Rc::downgrade(&anm0), Rc::downgrade(&game));
    let mut ecl_runner = EclRunner::new(&ecl, enemy.clone(), sub);

    assert_eq!(std::mem::size_of::<Vertex>(), std::mem::size_of::<FakeVertex>());
    let vertices: [Vertex; 4] = unsafe { std::mem::uninitialized() };

    let mut surface = GlfwSurface::new(WindowDim::Windowed(384, 448), "Touhou", WindowOpt::default()).unwrap();

    // Open the image atlas matching this ANM.
    let tex = load_from_disk(&mut surface, Path::new(png_filename)).expect("texture loading");

    // set the uniform interface to our type so that we can read textures from the shader
    let (program, _) =
        Program::<Semantics, (), ShaderInterface>::from_strings(None, VS, None, FS).expect("program creation");

    let mut tess = TessBuilder::new(&mut surface)
        .add_vertices(vertices)
        .set_mode(Mode::TriangleFan)
        .build()
        .unwrap();

    let mut back_buffer = Framebuffer::back_buffer(surface.size());

    'app: loop {
        for event in surface.poll_events() {
            match event {
                WindowEvent::Close | WindowEvent::Key(Key::Escape, _, Action::Release, _) => break 'app,

                WindowEvent::FramebufferSize(width, height) => {
                    back_buffer = Framebuffer::back_buffer([width as u32, height as u32]);
                }

                _ => (),
            }
        }

        if ecl_runner.running == false {
            break;
        }

        {
            let mut slice = tess
                .as_slice_mut()
                .unwrap();

            ecl_runner.run_frame();
            {
                let mut enemy = enemy.borrow_mut();
                enemy.update();
            }
            let mut game = game.borrow_mut();
            game.run_frame();
            let sprites = game.get_sprites();
            fill_vertices_ptr(sprites, slice.as_mut_ptr());
        }

        // here, we need to bind the pipeline variable; it will enable us to bind the texture to the GPU
        // and use it in the shader
        surface
            .pipeline_builder()
            .pipeline(&back_buffer, [0., 0., 0., 0.], |pipeline, shd_gate| {
                // bind our fancy texture to the GPU: it gives us a bound texture we can use with the shader
                let bound_tex = pipeline.bind_texture(&tex);

                shd_gate.shade(&program, |rdr_gate, iface| {
                    // update the texture; strictly speaking, this update doesn’t do much: it just tells the GPU
                    // to use the texture passed as argument (no allocation or copy is performed)
                    iface.color_map.update(&bound_tex);
                    //let mvp = ortho_2d(0., 384., 448., 0.);
                    let proj = perspective(0.5235987755982988, 384. / 448., 101010101./2010101., 101010101./10101.);
                    let view = setup_camera(0., 0., 1.);
                    let mvp = view * proj;
                    //println!("{:#?}", mvp);
                    // TODO: check how to pass by reference.
                    iface.mvp.update(*mvp.borrow_inner());

                    rdr_gate.render(RenderState::default(), |tess_gate| {
                        // render the tessellation to the surface the regular way and let the vertex shader’s
                        // magic do the rest!
                        tess_gate.render(&mut surface, (&tess).into());
                    });
                });
            });

        surface.swap_buffers();
    }
}

fn fill_vertices_ptr(sprites: Vec<(f32, f32, f32, Rc<RefCell<Sprite>>)>, vertices: *mut Vertex) {
    let mut fake_vertices = unsafe { std::mem::transmute::<*mut Vertex, &mut [FakeVertex; 4]>(vertices) };
    for (x, y, z, sprite) in sprites {
        let sprite = sprite.borrow();
        sprite.fill_vertices(&mut fake_vertices, x, y, z);
    }
}

fn load_from_disk(surface: &mut GlfwSurface, path: &Path) -> Option<Texture<Flat, Dim2, NormRGB8UI>> {
    // load the texture into memory as a whole bloc (i.e. no streaming)
    match image::open(&path) {
        Ok(img) => {
            let (width, height) = img.dimensions();
            let texels = img
                .pixels()
                .map(|(x, y, rgb)| (rgb[0], rgb[1], rgb[2]))
                .collect::<Vec<_>>();

            // create the luminance texture; the third argument is the number of mipmaps we want (leave it
            // to 0 for now) and the latest is a the sampler to use when sampling the texels in the
            // shader (we’ll just use the default one)
            let tex =
                Texture::new(surface, [width, height], 0, &Sampler::default()).expect("luminance texture creation");

            // the first argument disables mipmap generation (we don’t care so far)
            tex.upload(GenMipmaps::No, &texels);

            Some(tex)
        }

        Err(e) => {
            eprintln!("cannot open image {}: {}", path.display(), e);
            None
        }
    }
}
