# Xenoblade Importer For Noesis
Supports all 3 switch titles. Textures will be exported to the same folder as the exported mesh. During export it is recommended to set the scale to 100. Morph support and lower LODs are a toggle in the tools menu.


# DE and X3
Some meshes have shared skeletons. Under the tools menu you can manually specify the name of a chr file to use for the base skeleton.


# Known Bugs
* Due to the way the game has two skeletons that need merged, some meshes might end up with a twist bone parented to the root.

* Minor weight issues with eyes. Ive noticed that some eye shine parts sometimes get weighted to the wrong eye or in the case of a levnis it had its eye mesh weighted to the root. So far nothing major but still needs testing.
