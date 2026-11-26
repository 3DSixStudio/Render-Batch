**Render Batch v1.3.1** — skin renders

- Asset Render now knows the difference between **skins** (characters) and **objects** (eggs, blocks, items).
- **Asset type: Auto** (default) - an FBX with a rig (armature) or "-Loop" in its name is rendered as a skin.
- Skins: camera at eye level like a character portrait (Front 4°, 3/4 turned 22° at 6°), soft frontal light, smooth textures (no pixelation on clothes and faces).
- Objects keep the previous look: camera a bit from above (Front 8°, 3/4 turned 35° at 20°), sharp pixel textures.
- **Camera height** now defaults to **Auto** (the right angle for each type); set a number to override it.
- You can force Object or Skin for the whole folder with the Asset type option.
