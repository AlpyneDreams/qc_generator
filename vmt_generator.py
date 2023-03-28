import os
import subprocess
import bpy

from bpy.types import PropertyGroup, StringProperty, PointerProperty, CollectionProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator
from bpy.props import *

TEX_FILE_EXTS = ('.tga', '.psd')
VMT_FILE_EXT = '.vmt'

class VMT_Properties(PropertyGroup):
    tex_dir : StringProperty(
        name="Texture Folder",
        default="//"
    )


class VMT_OT_MakeVTF(Operator):
    """Compile an image to a VTF file"""
    bl_idname = "vmtgen.compile"
    bl_label = "Compile an image to a VTF"

    img_name : StringProperty(
        name="Image Name"
    )

    def execute(self, context):
        img = None
        for image in bpy.data.images:
            if image.name == self.img_name:
                img = image

        if img == None:
            self.report({'ERROR'}, "No image found with name: " + self.img_name)
            return {'FINISHED'}

        img_base = os.path.splitext(bpy.path.abspath(img.filepath))[0]
        img_path = None

        for ext in TEX_FILE_EXTS:
            if os.path.exists(img_base + ext):
                img_path = img_base + ext
                break

        if img_path == None:
            self.report({'ERROR'}, "No TGA or PSD found for {}. Save a copy of your image as a PSD or TGA! ".format(img_base))
            return {'FINISHED'}

        vtex_path = os.path.join(bpy.path.abspath(context.scene.vs.engine_path), "vtex.exe")
        if not os.path.exists(vtex_path):
            self.report({'ERROR'}, "Can't find vtex.exe: " + vtex_path)
            return {'FINISHED'}

        #self.report({'INFO'}, vtex_path)
        #self.report({'INFO'}, img_path)

        mat_path = os.path.join(context.scene.vs.game_path, 'materials', context.scene.qcgen.cdmaterials)

        print("Running vtex for \"{}\"...\n".format(os.path.basename(img_path)))
        vtex = subprocess.Popen([
            vtex_path,
            "-nopause",
            "-nop4",
            "-outdir", mat_path,
            img_path
        ])
        vtex.communicate()
        
        return{'FINISHED'}


class VMT_OT_MakeVMT(Operator):
    """Compile an image to a VMT file"""
    bl_idname = "vmtgen.generate"
    bl_label = "Generate a VMT file"

    mat_name: StringProperty(
        name="Image Name"
    )

    def execute(self, context):
        mat = None
        for m in bpy.data.materials:
            if m.name == self.mat_name:
                mat = m

        if mat == None:
            self.report(
                {'ERROR'}, "No material found with name: " + self.mat_name)
            return {'FINISHED'}

        mat_path = os.path.join(context.scene.vs.game_path, 'materials', context.scene.qcgen.cdmaterials)
        vmt_path = os.path.join(mat_path, mat.name + VMT_FILE_EXT)
        vtf_path = os.path.join(context.scene.qcgen.cdmaterials, os.path.splitext(os.path.basename(vmt_path))[0])

        #self.report({'INFO'}, vmt_path)

        # create if the VMT doesn't already exist 
        if not os.path.exists(vmt_path):
            f = open(vmt_path, 'w', encoding='utf8')
            def writef(args): print(args, file=f)
            writef('VertexLitGeneric')
            writef('{')
            writef('\t$basetexture "%s"' % vtf_path)
            writef('\t//$bumpmap "%s"' % (vtf_path + "_normal"))
            writef('}')
            f.close()
            self.report({'INFO'}, "VMT file has been created and can be viewed in the Text Editor.")
        else:
            self.report({'INFO'}, "VMT file has been opened and can be viewed in the Text Editor.")


        for area in bpy.context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                text_editor = area.spaces.active
                break
        else:
            text_editor = None
        
        vmt_name = mat.name + VMT_FILE_EXT
        for text in bpy.data.texts:
            if text.name.startswith(vmt_name):
                # vmt file is already open, switch to it
                if text_editor:
                    text_editor.text = text
                break
        else:
            # open the vmt file and show in text editor
            bpy.ops.text.open(filepath=vmt_path)
            if text_editor:
                text_editor.text = bpy.data.texts[vmt_name]

        return{'FINISHED'}


class VMT_PT_VMTPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "VMT/VTF Generator"
    bl_idname = "VMT_PT_VMTPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        vmtgen = context.scene.vmtgen
        
        layout.prop(context.scene.vs, 'game_path')
        layout.prop(context.scene.qcgen, 'cdmaterials')
        
        #mat_path = os.path.join(context.scene.vs.game_path, 'materials', context.scene.qcgen.cdmaterials)
        #layout.label(text=mat_path)

        layout.separator()
        layout.label(text="Compile VTF for Images: (Requires TGA/PSD file)")
        col = layout.column_flow(columns=2)
        for img in bpy.data.images:
            if img.type == 'IMAGE':
                col.operator('vmtgen.compile', text=bpy.path.basename(img.filepath), icon='IMAGE').img_name = img.name

        layout.separator()
        
        layout.label(text="Create/Open VMT for Materials:")
        col = layout.column_flow(columns=2)
        for mat in bpy.data.materials:
            col.operator('vmtgen.generate', text=mat.name, icon='MATERIAL').mat_name = mat.name






classes_vmt = (
    VMT_Properties,
    VMT_OT_MakeVTF,
    VMT_OT_MakeVMT,
    VMT_PT_VMTPanel
)
