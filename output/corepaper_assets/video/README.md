# Video Assets

- Base clips: generated with `scripts/vis/render_video.py`.
- Polished cut: generated with `scripts/vis/polish_video.py`.
- Full pipeline: `scripts/vis/build_video_pipeline.py`.
- Output format: MP4 only.

## Main Outputs

- Base manifest: `output/corepaper_assets/video/manifest.json`
- Pipeline manifest: `output/corepaper_assets/video/corepaper_video_pipeline_manifest.json`
- Polished MP4: `output/corepaper_assets/video/corepaper_video_polished.mp4`
- Submission MP4: `output/corepaper_submission/corepaper_video.mp4`

## Scenario Segments

- `META-shifted`: Baseline=0.1400, PPO-CVaR=0.4800, adaptmanip=0.6200, CORE=0.7200, Delta(CORE-Baseline)=+0.5800, Delta(CORE-PPO-CVaR)=+0.2400
- `S1-hard`: Baseline=0.5884, CORE=0.6436, Delta(CORE-Baseline)=+0.0551
- `S2-med`: Baseline=0.6696, CORE=0.7125, Delta(CORE-Baseline)=+0.0429
- `S3-severe`: Baseline=0.6444, CORE=0.6959, Delta(CORE-Baseline)=+0.0516
- `SIM-isaac`: Baseline=0.6258, PPO-CVaR=0.6659, CORE=0.6767, Delta(CORE-Baseline)=+0.0509, Delta(CORE-PPO-CVaR)=+0.0108
