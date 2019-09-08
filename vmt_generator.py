import os
import bpy

from bpy.types import PropertyGroup, StringProperty, PointerProperty, CollectionProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.props import *

class VMT_Properties(PropertyGroup):
    tex_dir : StringProperty(
        name="Texture Folder",
        default="//"
    )

class VMT_UL_TextureList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'

        type_icon = item.rna_type.properties['component_type'].enum_items.get(
            item.component_type).icon
        if type_icon:
            custom_icon = type_icon

        type_name = layout.enum_item_name(
            item, "component_type", item.component_type)

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text=type_name, icon=custom_icon)
            if item.component_type == 'collisionmodel':
                row.label(text="")
            else:
                row.label(text=item.name)

            if item.component_type == 'attachment':
                row.label(text=item.bone)
            else:
                row.label(text=item.path)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)


class VMT_PT_VMTPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "VMT/VTF Generator"
    bl_idname = "VMT_PT_VMTPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    tex_dir = None
    tex_cache = []

    def draw(self, context):
        layout = self.layout
        vmtgen = context.scene.vmtgen

        layout.prop(vmtgen, 'tex_dir')

        # when texture dir is changed, update cache of texture files
        if self.tex_dir != vmtgen.tex_dir:
            from glob import glob
            self.tex_cache = []
            path = bpy.path.abspath(vmtgen.tex_dir)
            
            # if the path is a directory, look at all files inside it
            if os.path.isdir(path):
                path = os.path.join(path, '*')
            
            for file in glob(path):
                self.tex_cache.append(file)
            self.tex_dir = vmtgen.tex_dir

        for tex in self.tex_cache:
            layout.label(text=tex)

        #for img in bpy.data.images:
        #    if img.filepath:
        #        layout.label(text=img.name)

        





classes_vmt = (
    VMT_Properties,

    VMT_UL_TextureList,
    VMT_PT_VMTPanel
)
