# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.storage.jsonstore import JsonStore
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.config import Config
from kivy.lang import Builder
from kivy.core.window import Window
import os
import mutagen
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.uix.popup import Popup

# 添加字体路径并注册中文字体
resource_add_path(os.path.abspath("./data/fonts"))
LabelBase.register("Roboto", "msyh.ttf") # 微软雅黑
# 添加字体路径并注册日文字体
LabelBase.register("NotoSansCJK", "NotoSansCJK-Regular.otf") # Noto Sans CJK

selected_musics = JsonStore('selected_musics.json')

class MusicItemLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MusicItemLayout, self).__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self.update_rect, pos=self.update_rect)
        self.orientation = 'horizontal'
        self.checkbox = CheckBox(size_hint=(0.1, 1))
        self.add_widget(self.checkbox)
        self.nameLabel = Label(text='', size_hint=(0.45, 1), color=(0, 0, 0, 1))
        self.add_widget(self.nameLabel)
        self.artistLabel = Label(text='', size_hint=(0.45, 1), color=(0, 0, 0, 1))
        self.add_widget(self.artistLabel)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        

class MainApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex('#A9A9A9')
        
        mainBox = BoxLayout(orientation='vertical')
        # search box
        self.searchBox = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.searchInput = TextInput(hint_text='Search for music...', size_hint=(0.8, 1))
        self.browseButton = Button(text='Browse', size_hint=(0.1, 1))
        self.browseButton.bind(on_press=self.on_browse_button_press)
        self.searchButton = Button(text='Search', size_hint=(0.1, 1))
        self.searchButton.bind(on_press=self.on_search_button_press)
        self.searchBox.add_widget(self.searchInput)
        self.searchBox.add_widget(self.browseButton)
        self.searchBox.add_widget(self.searchButton)
        mainBox.add_widget(self.searchBox)
        # music list
        self.musicScorllView = ScrollView(do_scroll_y=True, size_hint=(1, 0.8), bar_color=(0, 0, 0, 0.5), bar_inactive_color=(0, 0, 0, 0.2))
        self.musicListGrid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        with self.musicListGrid.canvas:
            Color(169/255, 169/255, 169/255, 1)
            self.rect = Rectangle(size=self.musicListGrid.size, pos=self.musicListGrid.pos)
            self.musicListGrid.bind(size=self.update_rect, pos=self.update_rect)
        self.musicListGrid.bind(minimum_height=self.musicListGrid.setter('height'))
        for music in selected_musics.keys():
            musicItem = MusicItemLayout(size_hint=(1, None), height=100)
            with musicItem.canvas:
                Color(1, 1, 1, 1)
            musicItem.nameLabel.text = selected_musics.get(music)['name']
            musicItem.artistLabel.text = selected_musics.get(music)['artist']
            musicItem.checkbox.active = selected_musics.get(music)['checked']
            musicItem.checkbox.bind(active=self.on_checkbox_active)
            self.musicListGrid.add_widget(musicItem)
        self.musicScorllView.add_widget(self.musicListGrid)
        mainBox.add_widget(self.musicScorllView)
        # m3u generate button
        self.m3uButton = Button(text='Generate M3U', size_hint=(1, 0.1))
        self.m3uButton.bind(on_press=self.on_m3u_button_press)
        mainBox.add_widget(self.m3uButton)
        return mainBox
    
    def update_rect(self, *args):
        self.rect.pos = self.root.pos
        self.rect.size = self.root.size
        
    def on_checkbox_active(self, checkbox, value):
        for music in selected_musics.keys():
            if selected_musics.get(music)['name'] == checkbox.parent.nameLabel.text and selected_musics.get(music)['artist'] == checkbox.parent.artistLabel.text:
                selected_musics.put(music, name=selected_musics.get(music)['name'], artist=selected_musics.get(music)['artist'], checked=value, path=selected_musics.get(music)['path'])
                break
            
    def on_browse_button_press(self, instance):
        filechooser = FileChooserListView(path='.', filters=['*.mp3', '*.flac', '*.wav'])
        popup = Popup(title='Browse Music Folder', size_hint=(0.9, 0.9))
        confirm_button = Button(text='Confirm', size_hint=(1, 0.1))
        confirm_button.bind(on_press=lambda x: self.on_filechooser_confirm(filechooser, popup))
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(filechooser)
        layout.add_widget(confirm_button)
        popup.content = layout
        popup.open()
    
    def on_filechooser_confirm(self, filechooser, popup):
        self.searchInput.text = str(filechooser.path).rsplit('/', 1)[0]
        popup.dismiss()

    def on_search_button_press(self, instance):
        path = self.searchInput.text
        selected_musics.clear()
        if os.path.isdir(path):
            self.musicListGrid.clear_widgets()
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.mp3') or file.endswith('.flac') or file.endswith('.wav'):
                        music_path = os.path.join(root, file)
                        music_item = mutagen.File(music_path, easy=True)
                        name = music_item.get('title', ['Unknown Title'])[0]
                        artist = music_item.get('artist', ['Unknown Artist'])[0]
                        selected_musics.put(music_path, name=name, artist=artist, checked=False, path=music_path)
                        musicItem = MusicItemLayout(size_hint=(1, None), height=100)
                        with musicItem.canvas:
                            Color(1, 1, 1, 1)
                        musicItem.nameLabel.text = name
                        musicItem.artistLabel.text = artist
                        musicItem.checkbox.active = False
                        musicItem.checkbox.bind(active=self.on_checkbox_active)
                        self.musicListGrid.add_widget(musicItem)
    
    def on_m3u_button_press(self, instance):
        root_path = selected_musics.get(list(selected_musics.keys())[0])['path'].split(selected_musics.get(list(selected_musics.keys())[0])['name'])[0]
        popup = Popup(title='Save M3U', size_hint=(0.5, 0.5))
        box = BoxLayout(orientation='vertical')
        path_input = TextInput(hint_text='Enter file name...', size_hint=(1, 0.8))
        save_button = Button(text='Save', size_hint=(1, 0.2))
        save_button.bind(on_press=lambda x: self.save_m3u(root_path + path_input.text, popup))
        box.add_widget(path_input)
        box.add_widget(save_button)
        popup.content = box
        popup.open()
        
    def save_m3u(self, file_name, popup):
        with open(f"{file_name}", 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for music in selected_musics.keys():
                if selected_musics.get(music)['checked']:
                    f.write(f'#EXTINF:-1,{selected_musics.get(music)["artist"]} - {selected_musics.get(music)["name"]}\n')
                    f.write(f'{selected_musics.get(music)["name"]}.{selected_musics.get(music)["path"].split(".")[-1]}\n')
        popup.dismiss()
        


app = MainApp()
app.run()