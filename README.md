# Vision-Based Autonomous Robot

An AI-vision robot that searches its surroundings, recognizes a person with a custom-trained YOLO model, and drives to them on its own while avoiding obstacles. Built in the Webots simulator for **Hack in Hills 2026**.

**Demo video:** https://drive.google.com/drive/folders/1rvAhJNhQGtnfwPMPPhANSpAtFgYrYmws?usp=drive_link



![Robot view with detection](docs/robot_view.png)



## How it works

```
Camera frame -> YOLO11s person detection -> bearing + distance estimate
             -> state machine (SEARCH / APPROACH / ARRIVED + sonar bypass)
             -> wheel speeds
```

- **Perception:** a YOLO11s model fine-tuned on simulator-generated images. Horizontal offset of the detection gives the bearing, and box height gives a distance cue.
- **Decision:** a small state machine searches for the person, drives toward them, and stops at a safe distance.
- **Obstacle avoidance:** the Pioneer 3-DX sonar ring triggers a back-off, turn and pass-by routine around boxes.
- **Recovery:** the robot rides out brief detection dropouts, reacquires the last-seen side, and uses a camera-based stuck detector to escape when it is pressed against something.
- **Stack:** Webots R2025a, Python 3.11, PyTorch (CUDA), Ultralytics YOLO11s, OpenCV.

## Training data without manual labeling

A Webots supervisor script (`controllers/data_collector`) teleports the robot, pedestrian and two boxes to random poses, captures the camera image, and computes the person's bounding box from the known 3D positions. About 800 labeled images were generated automatically, including frames that show only a box, so the model learns that boxes are not people. The first model reached 0.995 mAP50 on its simulated validation set (500 images); the final model uses the box-aware dataset. [ADD mAP50 FROM THE FINAL TRAINING SUMMARY]

## Results

Evaluated over 40 randomized trials in simulation (`controllers/trial_runner`, random seed 42). Each trial randomizes the robot start pose, the person's position, and both boxes' positions and angles. Timeout is 90 s of simulated time.

| Metric | Result |
|---|---|
| Reached the person and stopped safely | **37 / 40 (92.5%)** |
| Average time for successful trials | 45.6 s |
| Final distance to the person | 1.2 to 1.75 m |
| Trials where a box was touched or moved | 5 / 40 |

Success means the robot stopped within 2.5 m of the person and no closer than 0.6 m. A box counts as touched if it moved more than 3 cm or the robot's centre came within 0.6 m of it. Raw per-trial data: `results/trials.csv`.

## Known limitations

- **Sonar misses angled box corners:** a few trials brushed a box edge.
- **Hidden person:** if the person is behind a box, the robot may lose them and wander (one failure).
- **Slow bypass:** around two close obstacles, a trial can take 80 s or more.
- **Simulation only:** results are from Webots with one pedestrian model; real-world transfer is untested.

## Run it

1. Install Webots R2025a, Python 3.11, and PyTorch with CUDA from pytorch.org.
2. `pip install -r requirements.txt`
3. In Webots, open `worlds/hacknhills_sim.wbt`. Check that the Pioneer's `controller` is `vision_bot_v6`, then press Play.
   The controller loads `models/best.pt` automatically.

To rerun the evaluation, set the Pioneer's `controller` to `trial_runner` and `supervisor` to `TRUE`, make sure the nodes are named `PED`, `BOX1`, `BOX2`, and run in fast-forward. For dataset generation, use `data_collector` the same way (the camera node also needs the DEF name `CAM`).

## Repository layout

```
controllers/   vision_bot_v6 (robot), trial_runner (evaluation), data_collector (dataset generator)
worlds/        Webots world
models/        trained YOLO weights (best.pt)
results/       trial results
docs/          screenshots
data.yaml      dataset config for training
```

## Future work

- Camera-based obstacle cue to complement sonar
- Moving pedestrians and multiple people
- Natural-language goals ("go to the person in the red shirt")
- Metrics dashboard
- Transfer to a physical robot

## Team

[NAME 1] and [NAME 2], [COLLEGE]
