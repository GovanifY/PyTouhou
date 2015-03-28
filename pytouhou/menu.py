# -*- encoding: utf-8 -*-
##
## Copyright (C) 2014 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##

from pytouhou.utils.helpers import get_logger
logger = get_logger(__name__)

from gi.repository import Gtk, Gdk, GLib

import sys
import os
import re

GL_VERSION_REGEX = re.compile(r'^\d\.\d$')


class Handler:
    def __init__(self, config, args):
        self.config = config
        self.args = args

    def init_gtk(self, builder):
        self.start_window = builder.get_object('start_window')
        self.game_window = builder.get_object('game_window')
        self.options_window = builder.get_object('options_window')

        self.replay_filechooserdialog = builder.get_object('replay_filechooserdialog')

        # Game widgets
        self.difficulty_box = builder.get_object('difficulty_box')
        self.character_box = builder.get_object('character_box')
        self.stage_box = builder.get_object('stage_box')
        self.boss_rush_checkbutton = builder.get_object('boss_rush_checkbutton')

        self.difficulty_comboboxtext = builder.get_object('difficulty_comboboxtext')
        self.character_comboboxtext = builder.get_object('character_comboboxtext')
        self.stage_comboboxtext = builder.get_object('stage_comboboxtext')

        # Options widgets
        self.path_filechooserbutton = builder.get_object('path_filechooserbutton')
        self.backend_comboboxtext = builder.get_object('backend_comboboxtext')

        # OpenGL backend
        self.opengl_grid = builder.get_object('opengl_grid')
        self.flavor_comboboxtext = builder.get_object('flavor_comboboxtext')
        self.version_entry = builder.get_object('version_entry')
        self.double_buffer_checkbutton = builder.get_object('double_buffer_checkbutton')

        # SDL backend
        self.sdl_grid = builder.get_object('sdl_grid')

        self.fps_entry = builder.get_object('fps_entry')
        self.no_background_checkbutton = builder.get_object('no_background_checkbutton')
        self.no_particles_checkbutton = builder.get_object('no_particles_checkbutton')
        self.no_sound_checkbutton = builder.get_object('no_sound_checkbutton')

        self.difficulty_comboboxtext.set_active_id(str(self.args.rank))
        self.character_comboboxtext.set_active_id(str(self.args.character))
        self.stage_comboboxtext.set_active_id(str(self.args.stage))
        self.boss_rush_checkbutton.set_active(self.args.boss_rush)

        self.path_filechooserbutton.set_filename(self.args.path)
        self.backend_comboboxtext.set_active_id(' '.join(self.args.backend))

        self.flavor_comboboxtext.set_active_id(self.args.gl_flavor)
        self.version_entry.set_text(str(self.args.gl_version))
        if self.args.double_buffer is None:
            self.double_buffer_checkbutton.set_inconsistent(True)
        else:
            self.double_buffer_checkbutton.set_inconsistent(False)
            self.double_buffer_checkbutton.set_active(self.args.double_buffer)

        self.fps_entry.set_text(str(self.args.fps_limit))
        self.no_background_checkbutton.set_active(self.args.no_background)
        self.no_particles_checkbutton.set_active(self.args.no_particles)
        self.no_sound_checkbutton.set_active(self.args.no_sound)

    def hide_and_play(self, window):
        window.hide()
        Gtk.main_quit()
        print('Play!')

    def on_quit(self, *args):
        Gtk.main_quit(*args)
        sys.exit(0)


    # Main menu

    def on_start_window_key_press_event(self, window, event_key):
        if (event_key.keyval == Gdk.KEY_Escape or
                event_key.state == Gdk.ModifierType.CONTROL_MASK and event_key.keyval == Gdk.KEY_q):
            self.on_quit()

    def on_start_button_clicked(self, _):
        self.difficulty_box.show()
        self.character_box.show()
        self.stage_box.hide()

        self.stage_comboboxtext.set_active_id(None)
        self.args.stage = None

        self.start_window.hide()
        self.game_window.show()

    def on_extra_start_button_clicked(self, _):
        self.difficulty_box.hide()
        self.character_box.show()
        self.stage_box.hide()

        self.difficulty_comboboxtext.set_active_id('4')
        self.stage_comboboxtext.set_active_id('7')

        self.start_window.hide()
        self.game_window.show()

    def on_practice_start_button_clicked(self, _):
        self.difficulty_box.show()
        self.character_box.show()
        self.stage_box.show()

        self.start_window.hide()
        self.game_window.show()

    def on_options_button_clicked(self, _):
        self.start_window.hide()
        self.options_window.show()

    def on_replay_button_clicked(self, _):
        self.start_window.hide()
        self.replay_filechooserdialog.show()

    def on_inactive_button_clicked(self, _):
        raise NotImplementedError('Menu not implemented')

    on_netplay_start_button_clicked = on_inactive_button_clicked
    on_score_button_clicked = on_inactive_button_clicked
    on_music_room_button_clicked = on_inactive_button_clicked


    # Game menu

    def on_game_back_button_clicked(self, _):
        self.game_window.hide()
        self.start_window.show()

    def on_play_button_clicked(self, _):
        self.hide_and_play(self.game_window)

    def on_game_window_key_press_event(self, window, event_key):
        if event_key.keyval == Gdk.KEY_Escape:
            self.game_window.hide()
            self.start_window.show()
        elif event_key.state == Gdk.ModifierType.CONTROL_MASK and event_key.keyval == Gdk.KEY_q:
            self.on_quit()

    def on_difficulty_comboboxtext_changed(self, item):
        active = item.get_active_id()
        difficulty = int(active)
        self.config.set('rank', active if difficulty < 4 else None)
        self.args.rank = difficulty

    def on_character_comboboxtext_changed(self, item):
        character = int(item.get_active_id())
        self.config.set('character', character)
        self.args.character = character

    def on_stage_comboboxtext_changed(self, item):
        stage = item.get_active_id()
        self.args.stage = int(stage) if stage is not None else None

    def on_boss_rush_checkbutton_toggled(self, boss_rush_checkbutton):
        active = boss_rush_checkbutton.get_active()
        self.config.set('boss-rush', active)
        self.args.boss_rush = active


    # Replay dialog

    def on_replay_filechooserdialog_close(self, _):
        self.replay_filechooserdialog.hide()
        self.start_window.show()

    on_replay_cancel_button_clicked = on_replay_filechooserdialog_close

    def on_replay_open_button_clicked(self, button):
        try:
            open(self.args.replay, 'rb').close()
        except (IOError, TypeError):
            return
        self.hide_and_play(self.replay_filechooserdialog)

    def on_replay_filechooserdialog_selection_changed(self, dialog):
        self.args.replay = dialog.get_filename()

    def on_replay_filechooserdialog_file_activated(self, window):
        self.args.replay = window.get_filename()
        self.hide_and_play(self.replay_filechooserdialog)

    def on_replay_filechooserdialog_key_press_event(self, window, event_key):
        if event_key.keyval == Gdk.KEY_Escape:
            self.replay_filechooserdialog.hide()
            self.start_window.show()
        elif event_key.state == Gdk.ModifierType.CONTROL_MASK and event_key.keyval == Gdk.KEY_q:
            self.on_quit()


    # Options menu

    def on_options_back_button_clicked(self, _):
        self.options_window.hide()
        self.start_window.show()

    def on_options_window_key_press_event(self, window, event_key):
        if event_key.keyval == Gdk.KEY_Escape:
            self.options_window.hide()
            self.start_window.show()
        elif event_key.state == Gdk.ModifierType.CONTROL_MASK and event_key.keyval == Gdk.KEY_q:
            self.on_quit()

    def on_path_filechooserbutton_file_set(self, path_filechooserbutton):
        path = path_filechooserbutton.get_filename()
        self.config.set('path', path)

    def on_backend_comboboxtext_changed(self, backend_comboboxtext):
        active = backend_comboboxtext.get_active_id()
        self.config.set('backend', active)
        backends = active.split()
        new_grids = [getattr(self, backend + '_grid') for backend in backends]
        for grid in [self.opengl_grid, self.sdl_grid]:
            if grid not in new_grids:
                grid.hide()
            else:
                grid.show()

    def on_flavor_comboboxtext_changed(self, flavor_comboboxtext):
        active = flavor_comboboxtext.get_active_id()
        self.config.set('gl-flavor', active)

    def on_version_entry_changed(self, version_entry):
        text = version_entry.get_text()
        if not GL_VERSION_REGEX.match(text):
            raise ValueError('“%s” is not <digit>.<digit>' % text)
        self.config.set('gl-version', text)

    def on_double_buffer_checkbutton_clicked(self, double_buffer_checkbutton):
        inconsistent = double_buffer_checkbutton.get_inconsistent()
        active = double_buffer_checkbutton.get_active()
        if inconsistent:
            active = False
            inconsistent = False
        elif active:
            active = True
        else:
            inconsistent = True
        double_buffer_checkbutton.set_active(active)
        double_buffer_checkbutton.set_inconsistent(inconsistent)
        self.config.set('double-buffer', None if inconsistent else active)

    def on_fps_entry_changed(self, fps_entry):
        text = fps_entry.get_text()
        try:
            int(text)
        except ValueError:
            raise ValueError('“%s” is not integer' % text)
        else:
            self.config.set('fps-limit', text)

    def on_no_background_checkbutton_toggled(self, checkbutton):
        active = checkbutton.get_active()
        self.config.set('no-background', not active)

    def on_no_particles_checkbutton_toggled(self, checkbutton):
        active = checkbutton.get_active()
        self.config.set('no-particles', active)

    def on_no_sound_checkbutton_toggled(self, checkbutton):
        active = checkbutton.get_active()
        self.config.set('no-sound', active)


def menu(config, args):
    assert Gtk
    handler = Handler(config, args)

    builder = Gtk.Builder()
    try:
        builder.add_from_file(os.path.join(os.path.dirname(__file__), 'data', 'menu.glade'))
    except GLib.GError:
        builder.add_from_file(os.path.join('data', 'menu.glade'))
    builder.connect_signals(handler)

    handler.init_gtk(builder)

    Gtk.main()
