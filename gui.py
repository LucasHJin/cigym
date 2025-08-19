import os
import sys
import json
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsRectItem,
    QHBoxLayout,
    QGraphicsItem,
    QGraphicsLineItem,
    QComboBox,
    QLabel,
    QSizePolicy,
)
from PySide6.QtGui import QBrush, QColor, QCursor, QPainter, QFontMetrics, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from paths import add_io_dir
from combine import initial_processing, repeated_processing
import time

# MAYBE -> make it mark out the highlight places and let you adjust just like word blocks


# Model to map individual words on screen to the json
class WordBlock:
    def __init__(self, word, start, end, segment_id, word_index, importance):
        self.word = word
        self.start = start
        self.end = end
        self.segment_id = segment_id
        self.word_index = word_index
        self.importance = importance


# GUI block for each word
class DraggableWord(QGraphicsRectItem):
    RESIZE_THRESHOLD = 5
    SNAP_THRESHOLD = 5

    def __init__(self, word, time_scale=100):
        """Initializes a gui word block."""
        duration = word.end - word.start
        super().__init__(0, 0, duration * time_scale, 30)
        self.word = word
        self.time_scale = time_scale  # Zoom scale (pixels / second)
        self.setBrush(QBrush(QColor("#7f95e3")))
        # Make item draggable + resizeable
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        )
        self.resizing = False

    def mousePressEvent(self, event):
        """Handles state tracking for resizing vs dragging."""
        if event.pos().x() >= self.rect().width() - self.RESIZE_THRESHOLD:
            self.resizing = True
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        else:
            self.resizing = False
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handles actual resizing/dragging process."""
        if self.resizing:
            # Resizes + snaps to nearest block if necessary
            new_width = max(10, event.pos().x())
            snapped_width = self.get_snapped_width(new_width)
            self.setRect(0, 0, snapped_width, self.rect().height())
            self.word.end = self.word.start + snapped_width / self.time_scale
        else:
            # Drags block and updates timestamps
            super().mouseMoveEvent(event)
            duration = self.word.end - self.word.start
            self.setY(0)  # Lock vertical position
            # Snap to nearest block
            snapped_x = self.get_snapped_x(self.x(), duration)
            self.setX(snapped_x)
            self.word.start = max(0, snapped_x / self.time_scale)
            self.word.end = self.word.start + duration

    def mouseReleaseEvent(self, event):
        """Stop resizing mouse events."""
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.resizing = False
        super().mouseReleaseEvent(event)

    def get_snapped_x(self, proposed_x, duration):
        """
        Calculates distance of proposed block edges from other blocks to snap if necessary based on x position.
        For dragging events.
        """
        scene = self.scene()
        if not scene:
            return proposed_x

        my_left = proposed_x
        my_right = proposed_x + duration * self.time_scale

        for item in scene.items():
            if isinstance(item, DraggableWord) and item is not self:
                left = item.x()
                right = item.x() + item.rect().width()
                # Snap if close enough (smaller than snap threshold)
                if abs(my_left - left) < self.SNAP_THRESHOLD:
                    return left
                if abs(my_left - right) < self.SNAP_THRESHOLD:
                    return right
                if abs(my_right - left) < self.SNAP_THRESHOLD:
                    return left - duration * self.time_scale
                if abs(my_right - right) < self.SNAP_THRESHOLD:
                    return right - duration * self.time_scale
        return proposed_x

    def get_snapped_width(self, proposed_width):
        """
        Calculates distance of proposed block edges from other blocks to snap if necessary based on width.
        For resizing events.
        """
        scene = self.scene()
        if not scene:
            return proposed_width

        my_left = self.x()
        proposed_right = my_left + proposed_width

        for item in scene.items():
            if isinstance(item, DraggableWord) and item is not self:
                left = item.x()
                right = item.x() + item.rect().width()
                # Snap right edge
                if abs(proposed_right - left) < self.SNAP_THRESHOLD:
                    return left - my_left
                if abs(proposed_right - right) < self.SNAP_THRESHOLD:
                    return right - my_left
        return proposed_width

    def mouseDoubleClickEvent(self, event):
        """Opens dropdown to select importance level."""
        combo = QComboBox()
        combo.addItems(["1", "2", "3", "4"])
        combo.setCurrentText(str(self.word.importance))
        # Position dropdown box at mouse click
        view = self.scene().views()[0]
        pos = view.mapToGlobal(view.mapFromScene(event.scenePos()))
        combo.move(pos)
        combo.show()

        # Update importance if needed
        def update_importance(val):
            self.word.importance = int(val)
            combo.deleteLater()

        combo.currentTextChanged.connect(update_importance)

    def paint(self, painter: QPainter, option, widget=None):
        """Customizes how the wored block looks."""
        painter.setBrush(self.brush())
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawRect(self.rect())
        painter.setFont(QFont("Trebuchet MS", 16, QFont.Weight.Bold))
        painter.setPen(Qt.GlobalColor.white)
        font_metrics = QFontMetrics(painter.font())
        # Truncate text if necessary
        text = font_metrics.elidedText(
            self.word.word, Qt.TextElideMode.ElideRight, int(self.rect().width()) - 6
        )
        # Write word onto the block (center)
        painter.drawText(
            self.rect(),
            int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
            text,
        )


class SubtitleEditor(QWidget):
    def __init__(self):
        """Initializes the entire gui application window for cigym."""
        super().__init__()
        self.setWindowTitle("Cigym Subtitle Editor")
        self.resize(1200, 700)

        # State variables
        self.time_scale = 100
        self.words = []
        self.json_data = None
        self.playhead_dragging = False

        # Layouts
        main_layout = QVBoxLayout(
            self
        )  # Vertical main stack (video, control, timeline)
        control_layout = QVBoxLayout()  # Vertical buttons

        # Video (video, sound, playback)
        self.video_widget = QVideoWidget()
        main_layout.addWidget(self.video_widget)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.setSource(add_io_dir("output_subtitles.mp4"))
        self.player.pause()

        # Buttons + timer
        self.play_pause_btn = QPushButton("PLAY")
        self.export_btn = QPushButton("SAVE")
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.play_pause_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.zoom_in_btn)
        button_layout.addWidget(self.zoom_out_btn)

        control_layout = QVBoxLayout()
        control_layout.addLayout(button_layout)

        self.time_label = QLabel("0:00.00 / 0:00.00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        control_layout.addWidget(self.time_label)

        # Connect signals to buttons
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.export_btn.clicked.connect(self.save_changes)
        self.zoom_in_btn.clicked.connect(lambda: self.zoom(1.25))
        self.zoom_out_btn.clicked.connect(lambda: self.zoom(0.8))

        # Add control layout to main layout (do it down here so buttons appear after video)
        main_layout.addLayout(control_layout)

        # Timeline
        self.scene = QGraphicsScene()  # Scene for blocks and playhead
        self.view = QGraphicsView(self.scene)  # View to display scene
        self.view.setFixedHeight(80)
        main_layout.addWidget(self.view)
        self.view.viewport().installEventFilter(self)  # Function for moving playhead

        # Playhead
        self.playhead = QGraphicsLineItem(0, 0, 0, 40)
        self.playhead.setPen(QPen(QColor("red"), 2))
        self.scene.addItem(self.playhead)

        # Timer (to sync the playhead every 30ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_playhead)
        self.timer.start(30)

        # Load transcript
        self.load_json()
        self.draw_timeline()

    def toggle_play_pause(self):
        """Toggles between play/pause states."""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_pause_btn.setText("Play")
        else:
            self.player.play()
            self.play_pause_btn.setText("Pause")

    def zoom(self, factor):
        """Zooms in/out for the timeline by adjusting the time scale (how many px/sec)."""
        current_time = self.player.position() / 1000
        self.time_scale = max(20, min(500, int(self.time_scale * factor)))
        self.draw_timeline()
        pos = current_time * self.time_scale
        self.playhead.setLine(pos, 0, pos, 40)

    def load_json(self):
        """Creates word block instances from loaded JSON data."""
        with open(add_io_dir("transcript_processed.json"), "r") as f:
            self.json_data = json.load(f)

        self.words = []
        # Need segment and word index to be able to edit the json later on
        for seg_idx, segment in enumerate(self.json_data.get("segments", [])):
            for w_idx, w in enumerate(segment.get("words", [])):
                self.words.append(
                    WordBlock(
                        w["word"],
                        w["start"],
                        w["end"],
                        segment_id=seg_idx,
                        word_index=w_idx,
                        importance=w["importance"],
                    )
                )

    def export_json(self):
        """Updates the JSON with edited word block instance timestamps."""
        if not self.json_data:
            return
        for word in self.words:
            seg = self.json_data["segments"][word.segment_id]
            seg["words"][word.word_index]["start"] = word.start
            seg["words"][word.word_index]["end"] = word.end
            seg["words"][word.word_index]["importance"] = word.importance
        # Write changes to file
        with open(add_io_dir("transcript_processed.json"), "w") as f:
            json.dump(self.json_data, f, indent=2)
        print("Saved transcript_processed.json")

    def save_changes(self):
        """Save all changes and rerender the video."""
        self.player.pause()
        self.export_json()
        repeated_processing("output_subtitles_temp.mp4")

        # Make a unique filename to force reload
        temp_path = add_io_dir("output_subtitles_temp.mp4")
        timestamp = int(time.time() * 1000)
        final_path = add_io_dir(f"output_subtitles_{timestamp}.mp4")
        os.replace(temp_path, final_path)
        # Load into player
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(final_path))
        self.player.pause()

    def draw_timeline(self):
        """
        Redraws the timeline view (to be called when something changes).
        Note -> it only redraws dirty regions where something has changed, not entire timeline.
        """
        if self.json_data is None:
            return
        # Clear old items
        self.scene.clear()

        # Re add the background scene
        duration = self.player.duration() / 1000 if self.player.duration() > 0 else 40
        self.scene.setSceneRect(0, 0, duration * self.time_scale, 40)
        # Re add a new playhead
        self.playhead = QGraphicsLineItem(0, 0, 0, 40)
        self.playhead.setPen(QPen(QColor("red"), 2))
        self.scene.addItem(self.playhead)
        # Re add all the word block instances
        for word in self.words:
            rect = DraggableWord(word, self.time_scale)
            rect.setPos(word.start * self.time_scale, 0)
            self.scene.addItem(rect)

    def update_playhead(self):
        """
        Updates the position of the playhead based on the current playback position.
        """
        # Don't call this if the playhead is being dragged manually by user
        if self.playhead_dragging:
            return
        pos = self.player.position() / 1000
        self.playhead.setLine(pos * self.time_scale, 0, pos * self.time_scale, 40)

        # Update timer label
        duration = self.player.duration() / 1000 if self.player.duration() > 0 else 0
        self.time_label.setText(
            f"{self.format_time(pos)} / {self.format_time(duration)}"
        )

    def eventFilter(self, obj, event):
        """Filters mouse events in the timeline (i.e. clicking on a word block vs clicking on timeline vs dragging on timeline.)"""
        if obj is self.view.viewport():
            # If it's a click
            if event.type() == event.Type.MouseButtonPress:
                scene_pos = self.view.mapToScene(event.pos())
                item = self.scene.itemAt(scene_pos, self.view.transform())
                # If word block -> let it handle its own dragging/resizing
                if isinstance(item, DraggableWord):
                    return False
                # Else -> move playhead and playback
                x = max(0, min(scene_pos.x(), self.scene.width()))
                self.playhead.setLine(x, 0, x, 40)
                self.player.setPosition(int(x / self.time_scale * 1000))
                self.playhead_dragging = True
                return True
            # Update playhead and playback as dragging occurs
            elif event.type() == event.Type.MouseMove and self.playhead_dragging:
                scene_pos = self.view.mapToScene(event.pos())
                x = max(0, min(scene_pos.x(), self.scene.width()))
                self.playhead.setLine(x, 0, x, 40)
                self.player.setPosition(int(x / self.time_scale * 1000))
                return True
            # Stop dragging when mouse is released
            elif (
                event.type() == event.Type.MouseButtonRelease and self.playhead_dragging
            ):
                self.playhead_dragging = False
                return True

        # Fallback if nothing else
        return super().eventFilter(obj, event)

    def format_time(self, seconds):
        """Formats time in 0:00.00 to display video timeline."""
        m, s = divmod(seconds, 60)
        return f"{int(m)}:{s:05.2f}"


if __name__ == "__main__":
    initial_processing(2, 2.0)
    # Create application + main window
    app = QApplication(sys.argv)
    editor = SubtitleEditor()
    editor.show()
    sys.exit(app.exec())
