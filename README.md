# Blender QC, VMT, and VTF Generator

![](https://quak.ovh/3qFtkPD.png) ![](https://quak.ovh/8kKoSpe.png)

## Instructions

#### Blender QC Generator requires that you also have [Blender Source Tools](https://steamreview.org/BlenderSourceTools/) installed!

1. When your model is ready, set up everything you want as a separate SMD/DMX in its own collection.

2. Click on <kbd>Find Engine Path</kbd> in the **QC Generator** section of the **Properties Editor**'s **Scene** tab.

This will set the following options for Source Engine Export and QC Generator:

| Option           | Path                                                                                            |
|------------------|-------------------------------------------------------------------------------------------------|
| **Your .blend File** | `<root folder>\content\hl2mod\models\props_generic\television03\television03.blend` |
| Engine Path      | `<root folder>\game\bin`                                                           |
| Game Path        | `<root folder>\game\hl2mod`                                                         |
| MDL Name         | `props_generic\television03.mdl`                                                                |
| CD Materials     | `models\props_generic`                                                                          |

3. Set up your SMD/DMX models with Blender Source tools an export them all.

4. Set the parameters of your QC to generate, you can choose a model to be your collision model if desired, and then click <kbd>Write QC</kbd>

5. If you have `Open in Text Editor` checked then the generated QC file will open in a Blender text editor. If there is no Blender text editor on your screen, the largest area (usually the 3D view) will be changed to a text editor.

6. If you have `Automatically Overwrite File` checked then the QC file will be saved for you automatically.

7. You can then simply click on the QC file under the `Source Engine QC Compiles` section.

8. Congratulations, you've just fully compiled a MDL file! Open HLMV to see how it looks.

## VMT/VTF Generator

Click on the name of a texture to automatically run vtex with the correct output location for the VTF.

When you click on the name of a material, it'll look for a VMT file of the same name and open it as a text file in Blender that you can view in the Text Editor. 

* If that VMT does not exist a new simple one will be created.

## Troubleshooting

The <kbd>Find Engine Path</kbd> button will only work seamlessly if your blend file is in a folder like `<root>/content/<game>/<whatever>`, where `<root>` is some arbitrary folder, `<game>` is the name of your game (e.g. `hl2`) and there exists a source engine game folder (the one that would contain `GameInfo.txt`) in `<root>/game/<game>` and a bin folder with `studiomdl.exe` in `<root>/game/bin`.
