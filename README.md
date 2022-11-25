# Xenoblade Importer For Noesis
Supports all 3 switch titles. Textures will be exported to the same folder as the exported mesh. During export it is recommended to set the scale to 100. Morph support and lower LODs are a toggle in the tools menu.


# DE and X3
Some meshes have shared skeletons. Under the tools menu you can manually specify the name of a chr file to use for the base skeleton. The Chr file you want to use is going to be the lowest numbered file for the respective character. For example Shulk form DE would use pc010000 or Noah from X3 would use ch01011000


# Known Issues
* Due to the way the game has two skeletons that need merged, some meshes might end up with a twist bone parented to the root.

* Most weight issues should be fix but 1 or 2 might have slipped by

* On import into blender, some jaw bones might be rotated causing the inner mouth to stick out of the mesh slightly. Just reset the pose of the model to fix the issue. This is more on blender's side than noesis'

* When the skeleton isn't properly overridden on ch01011013, noesis gets stuck in an infinite export. Something in the weight data is causing the issue not noesis doens't seem to have a debug option to see exactly what is causing the issue.


# Recent Changes
* Rewrote a small portion of the image table reading. Should be more accurate and prevent some misc. items from only loading the lowest mip
* Added toggles to preview the vertex colors and to load in the duplicate meshes for things like outlines
____
* Small update to the lod handling to make it more accurate
* Minor tweak to image code to fix a few images exporting wrong
____
* Vertex colors no long preview over the mesh but will still be exported
* Some texture mirroring support was added DE mesh preview. It's not 100% accurate in detection but the meshes look a lot better than before
* Material color is now read
* Some work was put into fixing some of the misc weight errors that were appearing on eyes and other misc meshes
* Added the mesh index to the end of the mesh name. This will prevent meshes with the same material from being auto merged. Usefull for character meshes that have parts of their arm toggled for different customization
