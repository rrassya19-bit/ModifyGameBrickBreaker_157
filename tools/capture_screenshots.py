#!/usr/bin/env python3
"""Jalankan game dengan SDL dummy dan tangkap frame asli dari display."""

import os

# SDL harus memakai driver dummy sebelum pygame diimpor.
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import importlib.util
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
INITIAL_COMMIT = "8802652"
MAX_FRAMES = 6000
IMAGE_NAMES = (
    "before.png",
    "after_start.png",
    "after_game.png",
    "after_powerup.png",
    "after_gameover.png",
)


class FastClock:
    """Menghilangkan jeda frame tanpa mengubah alur update game."""

    def tick(self, _fps=0):
        return 0

    def get_fps(self):
        return 60


class KeyState:
    """Memberi input papan sesuai posisi bola yang sedang bergerak."""

    def __init__(self, pygame, tracker, mode):
        self.pygame = pygame
        self.tracker = tracker
        self.mode = mode

    def __getitem__(self, key):
        ball = self.tracker.get("ball")
        striker = self.tracker.get("striker")
        if ball is None or striker is None:
            return False

        if self.mode == "after_gameover":
            # Papan menjauh saat bola turun agar tiga nyawa habis alami.
            centre = striker.strikerRect.centerx
            if abs(ball.posx - centre) < 8:
                return key == (self.pygame.K_RIGHT
                               if striker.posx < 250
                               else self.pygame.K_LEFT)
            if ball.posx < centre:
                return key == self.pygame.K_RIGHT
            return key == self.pygame.K_LEFT

        # Untuk gameplay normal, papan mengikuti bola secara halus.
        target = ball.posx
        centre = striker.strikerRect.centerx
        if target < centre - 8:
            return key == self.pygame.K_LEFT
        if target > centre + 8:
            return key == self.pygame.K_RIGHT
        return False


def save_display(pygame, path):
    """Simpan display surface game yang sedang aktif ke PNG."""
    surface = pygame.display.get_surface()
    if surface is None:
        raise RuntimeError("Display game belum tersedia saat capture.")
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))


def load_game(mode, tracker):
    """Muat versi awal dari Git atau versi terkini tanpa mengedit app.py."""
    if mode == "before":
        source = subprocess.check_output(
            ["git", "show", f"{INITIAL_COMMIT}:app.py"], cwd=ROOT)
        temp_dir = Path(tempfile.mkdtemp(prefix="brickbreaker-before-"))
        tracker["source_tmp"] = temp_dir
        source_path = temp_dir / "app.py"
        source_path.write_bytes(source)
        spec = importlib.util.spec_from_file_location(
            "brickbreaker_before", source_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    sys.path.insert(0, str(ROOT))
    import app
    return app


def install_observers(pygame, game, mode, tracker):
    """Patch event, input, timer, dan display hanya di proses capture."""
    game.clock = FastClock()
    if hasattr(game, "loadHighScore"):
        # Skor pribadi tidak dibaca atau ditulis oleh sesi capture.
        game.loadHighScore = lambda: 0
        game.saveHighScore = lambda _score: None

    if hasattr(game, "POWERUP_CHANCE") and mode == "after_powerup":
        game.POWERUP_CHANCE = 1.0
    elif hasattr(game, "POWERUP_CHANCE") and mode == "after_game":
        game.POWERUP_CHANCE = 0.0

    original_get_pressed = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: KeyState(pygame, tracker, mode)
    original_event_get = pygame.event.get
    original_update = pygame.display.update
    original_flip = pygame.display.flip
    tracker["frame"] = 0
    tracker["space_sent"] = False
    tracker["quit_sent"] = False
    tracker["capture_path"] = ASSETS / (mode + ".png")
    tracker["captured"] = False

    if mode == "demo":
        tracker["gif_dir"] = Path(os.environ["CAPTURE_GIF_FRAMES"])
        tracker["gif_dir"].mkdir(parents=True, exist_ok=True)
        tracker["gif_frames"] = 0

    def observe_frame():
        tracker["frame"] += 1
        frame = tracker["frame"]
        if mode == "before" and frame == 90:
            save_display(pygame, tracker["capture_path"])
            tracker["captured"] = True

        if mode == "after_start" and frame == 95:
            save_display(pygame, tracker["capture_path"])
            tracker["captured"] = True

        ball = tracker.get("ball")
        if (mode == "after_game" and tracker.get("score_seen") and
                frame >= tracker.get("score_frame", frame) + 18):
            if ball is not None and len(getattr(ball, "trail", ())) >= 4:
                if not tracker["captured"]:
                    save_display(pygame, tracker["capture_path"])
                    tracker["captured"] = True

        if mode == "after_powerup" and not tracker["captured"]:
            active_powerup = any(
                0 <= powerup.posy < 450
                for powerup in tracker.get("powerups", []))
            active_particle = any(
                particle.life > 0
                for particle in tracker.get("particles", []))
            active_shockwave = any(
                wave.life > 0
                for wave in tracker.get("shockwaves", []))
            if active_powerup and active_particle and active_shockwave:
                save_display(pygame, tracker["capture_path"])
                tracker["captured"] = True

        if mode == "after_gameover" and not tracker["captured"]:
            started = tracker.get("gameover_frame")
            if started is not None and frame >= started + 35:
                save_display(pygame, tracker["capture_path"])
                tracker["captured"] = True

        if mode == "demo" and tracker.get("ball_updates", 0) > 0:
            # 75 frame samples every four game frames produce five seconds at 15 FPS.
            if tracker["ball_updates"] % 4 == 0:
                if tracker["last_gif_ball_frame"] != tracker["ball_updates"]:
                    index = tracker["gif_frames"]
                    if index < 75:
                        frame_path = tracker["gif_dir"] / f"frame-{index:03d}.png"
                        save_display(pygame, frame_path)
                        tracker["gif_frames"] += 1
                        tracker["last_gif_ball_frame"] = tracker["ball_updates"]

        if (mode in ("after_game", "after_powerup") and
                tracker.get("captured") and not tracker["quit_sent"]):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            tracker["quit_sent"] = True

        if frame >= MAX_FRAMES and not tracker["quit_sent"]:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            tracker["quit_sent"] = True

    def update(*args, **kwargs):
        result = original_update(*args, **kwargs)
        observe_frame()
        return result

    def flip():
        result = original_flip()
        observe_frame()
        return result

    pygame.display.update = update
    pygame.display.flip = flip

    def event_get(*args, **kwargs):
        frame = tracker["frame"]
        events = []
        if mode == "before" and frame >= 110 and not tracker["quit_sent"]:
            events.append(pygame.event.Event(pygame.QUIT))
            tracker["quit_sent"] = True
        elif mode == "after_start" and frame >= 115 and not tracker["space_sent"]:
            events.append(pygame.event.Event(
                pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" "))
            tracker["space_sent"] = True
        elif mode in ("after_game", "after_powerup", "after_gameover", "demo"):
            if frame >= 115 and not tracker["space_sent"]:
                events.append(pygame.event.Event(
                    pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" "))
                tracker["space_sent"] = True

            gameover_frame = tracker.get("gameover_frame")
            if (mode == "after_gameover" and gameover_frame is not None and
                    frame >= gameover_frame + 65 and not tracker["quit_sent"]):
                events.append(pygame.event.Event(
                    pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode=""))
                tracker["quit_sent"] = True

            if mode == "demo" and tracker.get("gif_frames", 0) >= 75:
                if not tracker["quit_sent"]:
                    events.append(pygame.event.Event(pygame.QUIT))
                    tracker["quit_sent"] = True

        events.extend(original_event_get(*args, **kwargs))
        return events

    pygame.event.get = event_get

    if mode != "before":
        tracker["ball_updates"] = 0
        tracker["last_gif_ball_frame"] = -1

        def observe_constructor(class_name, list_key=None):
            cls = getattr(game, class_name)
            original_init = cls.__init__

            def wrapped_init(instance, *args, **kwargs):
                original_init(instance, *args, **kwargs)
                if class_name == "Ball":
                    tracker["ball"] = instance
                elif class_name == "Striker":
                    tracker["striker"] = instance
                elif list_key:
                    tracker.setdefault(list_key, []).append(instance)

            cls.__init__ = wrapped_init

        observe_constructor("Ball")
        observe_constructor("Striker")
        observe_constructor("PowerUp", "powerups")
        observe_constructor("Particle", "particles")
        observe_constructor("Shockwave", "shockwaves")

        original_ball_update = game.Ball.update

        def ball_update(instance, *args, **kwargs):
            tracker["ball"] = instance
            result = original_ball_update(instance, *args, **kwargs)
            tracker["ball_updates"] += 1
            return result

        game.Ball.update = ball_update

        original_get_score = game.Block.getScore

        def get_score(instance, *args, **kwargs):
            tracker["score_seen"] = True
            tracker.setdefault("score_frame", tracker["frame"])
            return original_get_score(instance, *args, **kwargs)

        game.Block.getScore = get_score

        original_game_over = game.gameOver

        def game_over(*args, **kwargs):
            tracker["gameover_frame"] = tracker["frame"]
            return original_game_over(*args, **kwargs)

        game.gameOver = game_over

    # Menahan variable asli agar patch input tetap bisa dipulihkan saat worker berakhir.
    tracker["original_get_pressed"] = original_get_pressed


def run_worker(mode):
    import pygame

    random.seed(157)
    tracker = {"mode": mode, "score_seen": False}
    game = load_game(mode, tracker)
    install_observers(pygame, game, mode, tracker)

    try:
        if mode == "before":
            game.main()
        elif mode == "after_start":
            game.startScreen(0)
        else:
            if mode == "demo":
                tracker["score_seen"] = False
            game.main()
    finally:
        pygame.quit()
        source_tmp = tracker.get("source_tmp")
        if source_tmp is not None:
            shutil.rmtree(source_tmp, ignore_errors=True)

    if mode != "demo" and not tracker.get("captured"):
        raise RuntimeError(
            f"Screenshot {mode}.png gagal; frame={tracker.get('frame')}, "
            f"bola bergerak={tracker.get('ball_updates', 0)}, "
            f"skor terlihat={tracker.get('score_seen')}, "
            f"power-up={len(tracker.get('powerups', []))}, "
            f"game over={tracker.get('gameover_frame')}.")

    if mode == "demo" and tracker.get("gif_frames", 0) < 75:
        raise RuntimeError(
            f"GIF hanya memiliki {tracker.get('gif_frames', 0)} frame capture.")
    print(f"worker {mode}: frame={tracker.get('frame')}, "
          f"capture={tracker.get('captured')}, "
          f"gif_frames={tracker.get('gif_frames', 0)}")


def create_demo_gif(frame_dir):
    """Rangkai frame game asli menjadi GIF 15 FPS jika Pillow tersedia."""
    try:
        from PIL import Image
    except ImportError:
        print("GIF dilewati: Pillow tidak tersedia (pip install pillow).")
        return False

    frames = []
    for path in sorted(frame_dir.glob("frame-*.png")):
        with Image.open(path) as source:
            frame = source.convert("RGB")
            if frame.width > 600:
                height = round(frame.height * 600 / frame.width)
                frame = frame.resize((600, height), Image.Resampling.LANCZOS)
            frames.append(frame.quantize(colors=96, method=Image.Quantize.FASTOCTREE))

    if len(frames) < 75:
        print(f"GIF dilewati: frame gameplay tersedia hanya {len(frames)}.")
        return False

    output = ASSETS / "demo.gif"
    frame_durations = [60 if index % 3 == 0 else 70
                       for index in range(len(frames))]
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=frame_durations, loop=0,
                   optimize=True, disposal=2)
    if output.stat().st_size >= 5 * 1024 * 1024:
        output.unlink()
        print("GIF dilewati: hasil optimasi masih mencapai 5 MB.")
        return False
    return True


def verify_images():
    """Cek ukuran PNG serta variasi warna agar file tidak kosong/hitam."""
    import pygame

    pygame.init()
    for name in IMAGE_NAMES:
        path = ASSETS / name
        if not path.is_file() or path.stat().st_size < 1000:
            raise RuntimeError(f"File screenshot tidak ada/kosong: {path}")
        surface = pygame.image.load(str(path))
        if surface.get_width() < 300 or surface.get_height() < 250:
            raise RuntimeError(f"Ukuran screenshot tidak wajar: {name}")
        colors = set()
        visible_samples = 0
        for y in range(0, surface.get_height(), 5):
            for x in range(0, surface.get_width(), 5):
                color = surface.get_at((x, y))[:3]
                colors.add(color)
                if color != (0, 0, 0):
                    visible_samples += 1
        if len(colors) < 3 or visible_samples < 1000:
            raise RuntimeError(f"Screenshot terlalu hitam/kosong: {name}")
        print(f"verified {name}: {surface.get_width()}x{surface.get_height()}, "
              f"{path.stat().st_size} bytes, {len(colors)} sampled colors")
    pygame.quit()


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    highscore = ROOT / "highscore.txt"
    highscore_state = (highscore.exists(), highscore.read_bytes()
                       if highscore.exists() else None)

    temp_root = Path(tempfile.mkdtemp(prefix="brickbreaker-capture-"))
    modes = ("before", "after_start", "after_game", "after_powerup",
             "after_gameover")
    try:
        for mode in modes:
            print(f"Menjalankan capture {mode}...")
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--worker", mode],
                cwd=ROOT, check=False, timeout=120)
            if result.returncode:
                raise RuntimeError(
                    f"Capture {mode} gagal dengan status {result.returncode}.")

        gif_frames = temp_root / "gif-frames"
        print("Menjalankan capture frame demo...")
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", "demo"],
            cwd=ROOT, env={**os.environ, "CAPTURE_GIF_FRAMES": str(gif_frames)},
            check=False, timeout=120)
        if result.returncode == 0:
            create_demo_gif(gif_frames)
        else:
            print(f"GIF dilewati: sesi gameplay demo gagal ({result.returncode}).")

        verify_images()
    finally:
        current_state = (highscore.exists(), highscore.read_bytes()
                         if highscore.exists() else None)
        if current_state != highscore_state:
            if highscore_state[0]:
                highscore.write_bytes(highscore_state[1])
            elif highscore.exists():
                highscore.unlink()
            raise RuntimeError("highscore.txt berubah; salinan awal dipulihkan.")
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        run_worker(sys.argv[2])
    else:
        main()
