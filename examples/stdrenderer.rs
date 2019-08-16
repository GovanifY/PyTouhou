use image::GenericImageView;
use luminance::context::GraphicsContext;
use luminance::framebuffer::Framebuffer;
use luminance::pipeline::BoundTexture;
use luminance::pixel::{NormRGB8UI, Floating};
use luminance::render_state::RenderState;
use luminance::shader::program::{Program, Uniform};
use luminance::tess::{Mode, TessBuilder, TessSliceIndex};
use luminance::texture::{Dim2, Flat, Sampler, Texture, GenMipmaps};
use luminance_derive::{Semantics, Vertex, UniformInterface};
use luminance_glfw::event::{Action, Key, WindowEvent};
use luminance_glfw::surface::{GlfwSurface, Surface, WindowDim, WindowOpt};
use touhou::th06::anm0::Anm0;
use touhou::th06::anm0_vm::{AnmRunner, Sprite, Vertex as FakeVertex};
use touhou::th06::std::{Stage, Position};
use touhou::th06::std_vm::StageRunner;
use touhou::util::prng::Prng;
use touhou::util::math::perspective;
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
uniform vec3 instance_position;

out vec2 texcoord;
out vec4 color;

void main()
{
    vec3 position = vec3(in_position) + instance_position;
    gl_Position = mvp * vec4(position, 1.0);
    texcoord = vec2(in_texcoord);

    // Normalized from the u8 being passed.
    color = vec4(in_color) / 255.;
}
"#;

const FS: &str = r#"
in vec2 texcoord;
in vec4 color;

uniform sampler2D color_map;
uniform float fog_scale;
uniform float fog_end;
uniform vec4 fog_color;

out vec4 frag_color;

void main()
{
    vec4 temp_color = texture(color_map, texcoord) * color;
    float depth = gl_FragCoord.z / gl_FragCoord.w;
    float fog_density = clamp((fog_end - depth) * fog_scale, 0.0, 1.0);
    frag_color = vec4(mix(fog_color, temp_color, fog_density).rgb, temp_color.a);
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

    #[uniform(name = "instance_position")]
    instance_position: Uniform<[f32; 3]>,

    #[uniform(name = "fog_scale")]
    fog_scale: Uniform<f32>,

    #[uniform(name = "fog_end")]
    fog_end: Uniform<f32>,

    #[uniform(name = "fog_color")]
    fog_color: Uniform<[f32; 4]>,
}

fn main() {
    // Parse arguments.
    let args: Vec<_> = env::args().collect();
    if args.len() != 4 {
        eprintln!("Usage: {} <STD file> <ANM file> <PNG file>", args[0]);
        return;
    }
    let std_filename = &args[1];
    let anm_filename = &args[2];
    let png_filename = &args[3];

    // Open the STD file.
    let file = File::open(std_filename).unwrap();
    let mut file = BufReader::new(file);
    let mut buf = vec![];
    file.read_to_end(&mut buf).unwrap();
    let (_, stage) = Stage::from_slice(&buf).unwrap();

    // Open the ANM file.
    let file = File::open(anm_filename).unwrap();
    let mut file = BufReader::new(file);
    let mut buf = vec![];
    file.read_to_end(&mut buf).unwrap();
    let anm0 = Anm0::from_slice(&buf).unwrap();

    // TODO: seed this PRNG with a valid seed.
    let prng = Rc::new(RefCell::new(Prng::new(0)));

    assert_eq!(std::mem::size_of::<Vertex>(), std::mem::size_of::<FakeVertex>());
    let mut vertices: Vec<Vertex> = vec![];
    let mut indices = vec![];

    {
        for model in stage.models.iter() {
            let begin = vertices.len();
            for quad in model.quads.iter() {
                let Position { x, y, z } = quad.pos;

                // Create the AnmRunner from the ANM and the sprite.
                let sprite = Rc::new(RefCell::new(Sprite::new()));
                let _anm_runner = AnmRunner::new(&anm0, quad.anm_script as u8, sprite.clone(), Rc::downgrade(&prng), 0);
                let mut new_vertices: [Vertex; 6] = unsafe { std::mem::uninitialized() };
                fill_vertices(sprite.clone(), &mut new_vertices, x, y, z);
                new_vertices[4] = new_vertices[0];
                new_vertices[5] = new_vertices[2];
                vertices.extend(&new_vertices);
            }
            let end = vertices.len();
            indices.push((begin, end));
        }
    }

    let mut stage_runner = StageRunner::new(Rc::new(RefCell::new(stage)));

    let mut surface = GlfwSurface::new(WindowDim::Windowed(384, 448), "Touhou", WindowOpt::default()).unwrap();

    // Open the image atlas matching this ANM.
    let tex = load_from_disk(&mut surface, Path::new(png_filename)).expect("texture loading");

    // set the uniform interface to our type so that we can read textures from the shader
    let (program, _) =
        Program::<Semantics, (), ShaderInterface>::from_strings(None, VS, None, FS).expect("program creation");

    let tess = TessBuilder::new(&mut surface)
        .add_vertices(vertices)
        .set_mode(Mode::Triangle)
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

        {
            stage_runner.run_frame();
            //let sprites = stage.get_sprites();
            //fill_vertices_ptr(sprites, slice.as_mut_ptr());
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

                    let proj = perspective(0.5235987755982988, 384. / 448., 101010101./2010101., 101010101./10101.);
                    let model_view = stage_runner.get_model_view();
                    let mvp = model_view * proj;
                    // TODO: check how to pass by reference.
                    iface.mvp.update(*mvp.borrow_inner());

                    let near = stage_runner.fog_near - 101010101. / 2010101.;
                    let far = stage_runner.fog_far - 101010101. / 2010101.;
                    iface.fog_color.update(stage_runner.fog_color);
                    iface.fog_scale.update(1. / (far - near));
                    iface.fog_end.update(far);

                    let stage = stage_runner.stage.borrow();
                    for instance in stage.instances.iter() {
                        iface.instance_position.update([instance.pos.x, instance.pos.y, instance.pos.z]);

                        rdr_gate.render(RenderState::default(), |tess_gate| {
                            let (begin, end) = indices[instance.id as usize];
                            tess_gate.render(&mut surface, tess.slice(begin..end));
                        });
                    }
                });
            });

        surface.swap_buffers();
    }
}

fn fill_vertices(sprite: Rc<RefCell<Sprite>>, vertices: &mut [Vertex; 6], x: f32, y: f32, z: f32) {
    let mut fake_vertices = unsafe { std::mem::transmute::<&mut [Vertex; 6], &mut [FakeVertex; 4]>(vertices) };
    let sprite = sprite.borrow();
    sprite.fill_vertices(&mut fake_vertices, x, y, z);
}

fn load_from_disk(surface: &mut GlfwSurface, path: &Path) -> Option<Texture<Flat, Dim2, NormRGB8UI>> {
    // load the texture into memory as a whole bloc (i.e. no streaming)
    match image::open(&path) {
        Ok(img) => {
            let (width, height) = img.dimensions();
            let texels = img
                .pixels()
                .map(|(_x, _y, rgb)| (rgb[0], rgb[1], rgb[2]))
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
