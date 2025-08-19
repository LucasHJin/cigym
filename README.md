# CIGYM – Cinematic Gym Videos

**Cigym** is a Python-based tool designed to automate the creation of high-quality, cinematic gym edits. It allows users to generate dynamic edits with synced music, transitions, and animated text overlays, all with minimal manual intervention.

---

## Sample Result

![Demo](assets/sample_video.gif)

*Note that the video quality only looks worse because it is displayed as a GIF for the purpose this README.* 

---

## Functionality

- **Automatic Clipping**
  The most important parts of an audio are detected and used as markers to clip together videos.

- **Animated Text Effects**
  The lyrics of any sound are automatically detected and shown in the video at their desired timestamps with the following effects:
  - 50+ font styles
  - Rapidly changing text
  - Text behind a person

- **Filter Application**
  A custom Ffmpeg command is run to turn any video into a more cinematic experience by colour grading, changing brightness, etc.
fading, and volume adjustments

- **GUI Support**  
  Interactive interface to:  
  - Preview edits in real-time  
  - Adjust text style and timestamps
    - Automatic text snapping for a clean editing experience

---

## Installation

### Requirements
- Python 3.10+  
- FFmpeg installed and added to your system PATH  

### Setup
1. Clone this repository:
```bash
git clone https://github.com/yourusername/gym-video-editor.git
cd gym-video-editor
```
2. Ensure FFmpeg is installed and accessible from your terminal  
3. Install all the dependencies
```bash
pip install -r requirements.txt
```
4. Launch the GUI:
```bash
python gui.py
```
5. For any custom changes/scripting (i.e. manually changing highlight locations), locate the ```combine.py``` file and run the ```manual_highlight_processing()``` function.
6. The finished result will be located in ```/io_files``` as the most recent ```output_subtitles*.mp4```.

---

## Credits

- **Developer**: [Lucas Jin](mailto:lucasjin.hh@gmail.com)
- **Libraries & Tools**:  
  - [FFmpeg](https://ffmpeg.org/) – video/audio processing  
  - [PySide6](https://doc.qt.io/qtforpython-6/gettingstarted.html#getting-started) – GUI framework  
  - [NumPy](https://numpy.org/) – audio and video analysis  
  - [SciPy](https://scipy.org/) – highlight detection & waveform analxysis
  - [Robust Video Matting](https://github.com/PeterL1n/RobustVideoMatting)  - model to remove background

---

## Additional Notes

- **Cross-platform**: Works on Windows, macOS, and Linux  
- **Customization**: All text styles, transitions, and audio settings are configurable via GUI or script parameters  