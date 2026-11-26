**Render Batch v1.2.0** — new Asset Render page

- New **Asset Render** page in the sidebar: choose a folder of **FBX** files and the app sets up everything and renders them for you.
- Camera **3/4 view** or **Front view** (adjustable height). The camera automatically fits every asset inside the frame with a margin you choose, nothing gets cropped.
- Automatic lighting (key / fill / rim + ambient) for bright, vivid icons; adjustable light strength.
- Parents are rendered together with all their children. Animated files (e.g. *-Loop-Idle*) are posed at their first frame.
- Image name = FBX name; everything from "-Loop" is removed: `Boy-Loop-Idle.fbx` → `Boy.png`.
- Transparent background, sharp pixel textures, image size, frame margin, Cycles / EEVEE and samples are all adjustable.
- Tick which FBX files to render; ticks are remembered per folder. Drag a folder onto the page to load it.
