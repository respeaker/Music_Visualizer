Music Visualizer
================

## For ReSpeaker

![](light_music_player_preview.jpg)

```
wget https://github.com/respeaker/muisic_visualizer/raw/master/light_music_player.py
python light_music_player.py music.wav
```


## For Windows/Linux

![](preview.gif)

### music_visualizer.py
Requirements

+ FFTW3
+ PySide
+ PyAudio


```
python music_visualizer music.wav
```

### player_with_spectrum.py
Requirements

+ gstreamer
+ gst-python
+ python-gi
+ pyside


```
python player_with_spectrum.py music.mp3
```