import bpy

from bpy.types import PropertyGroup, StringProperty, PointerProperty, CollectionProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator
from bpy.props import *

import imp, sys, os
for filename in [ f for f in os.listdir(os.path.dirname(os.path.realpath(__file__))) if f.endswith(".py") ]:
	if filename == os.path.basename(__file__): continue
	mod = sys.modules.get("{}.{}".format(__name__,filename[:-3]))
	if mod: imp.reload(mod)

bl_info = {
    "name": "QC Generator",
    "author": "Alpyne",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic"
}

#region QC Datamodel Structs

class QC_Body(PropertyGroup):
    name : StringProperty(
        name="Name", default="body")
    path : StringProperty(
        name="Path", default="reference.smd")
    component_type : EnumProperty(
        name="Component Type",
        items=(
            ('body', "Body", "Body", 'OBJECT_DATAMODE', 0),
            ('model', "Model", "Model", 'ARMATURE_DATA', 1),
            ('collisionmodel', "Collision", "Collision Model", 'MESH_DATA', 2),
            ('attachment', "Attachment", "Attachment Point", 'EMPTY_ARROWS', 3),
            ('sequence', "Sequence", "Sequence", "ANIM", 4)
        ),
        default="body"
    )

    # collisionmodel
    mass: FloatProperty(
        name="Mass"
    )

    # attachment
    bone: StringProperty(
        name="Bone"
    )
    

class QC_Properties(PropertyGroup):
    modelname: StringProperty(
        name="MDL Name", description="The path of the .mdl file relative to the models/ dir.")
    cdmaterials: StringProperty(
        name="CD Materials", description="The path of the model's materials relative to the materials/ dir.",
        default="models/")
    bodies: CollectionProperty(
        name="Bodies", type=QC_Body)
    bodies_active: IntProperty(
        name="Selected Body", default=0, min=0, options={'HIDDEN'})  # , update=bodies_active_changed)
    staticprop: BoolProperty(
        name="Static Prop", default=False)
    scale: IntProperty(
        name="Scale",
        default=0
    )
    surfaceprop: StringProperty(
        name="Surface Property"
    )
    contents: EnumProperty(
        name="Contents",
        items=(
            ('grate', "Grate", "Not solid to bullets or line-of-sight."),
            ('monster', "NPC", "NPC solidity type"),
            ('notsolid', "Not Solid", "Not solid to anything."),
            ('solid', "Solid", "Default behavior, solid to everything."),
            ('ladder', "Ladder", "Ladder"),
        ),
        default="solid"
    )

    

#endregion

#region Body List + Operators

class QC_UL_BodyList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'

        type_icon = item.rna_type.properties['component_type'].enum_items.get(item.component_type).icon
        if type_icon: custom_icon = type_icon

        type_name = layout.enum_item_name(item, "component_type", item.component_type)

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
            
class QC_OT_AddBody(Operator):
    bl_idname = "bodies.add"
    bl_label = "Add a new body"

    def execute(self, context):
        context.scene.qcgen.bodies.add()

        # auto-select the newly added component
        context.scene.qcgen.bodies_active = len(context.scene.qcgen.bodies) - 1

        return{'FINISHED'}

class QC_OT_RemoveBody(Operator):
    bl_idname = "bodies.remove"
    bl_label = "Removes a body"

    @classmethod
    def poll(cls, context):
        return context.scene.qcgen.bodies

    def execute(self, context):
        bodies = context.scene.qcgen.bodies
        index = context.scene.qcgen.bodies_active

        bodies.remove(index)
        context.scene.qcgen.bodies_active = min(max(0, index - 1), len(bodies) - 1)

        return{'FINISHED'}

class QC_OT_MoveBody(Operator):
    """Move an item in the list."""

    bl_idname = "bodies.move_item"
    bl_label = "Move an item in the list"

    direction : bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.qcgen.bodies

    def move_index(self):
        """ Move index of an item render queue while clamping it. """

        index = bpy.context.scene.qcgen.bodies_active
        list_length = len(bpy.context.scene.qcgen.bodies) - 1  # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.qcgen.bodies_active = max(0, min(new_index, list_length))

    def execute(self, context):
        bodies = context.scene.qcgen.bodies
        index = context.scene.qcgen.bodies_active

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        bodies.move(neighbor, index)
        self.move_index()

        return{'FINISHED'} 
# endregion

class QC_OT_WriteQC(Operator):
    bl_idname = "qcgen.write"
    bl_label = "Write QC File"

    def execute(self, context):
        from .qcfile import write_qc_file
        write_qc_file(context.scene.qcgen)
        return{'FINISHED'}

class QC_OT_AutofillVS(Operator):
    bl_idname = "qcgen.autofill_vs"
    bl_label = "Autofill Blender Source Tools paths"
    
    def execute(self, context):
        #print()
        if not context.scene.vs:
            return{'FINISHED'}
        
        # root/content/modelsrc/props_c17
        curdir = os.path.dirname(bpy.data.filepath)

        i = curdir.find('content')

        if i < 0:
            self.report({'ERROR'}, "Your current path does not have a 'content' folder.")
            return{'FINISHED'}

        j = i + len('content') + 1
        k = j + curdir[j:].replace('\\', '/').find('/')
        
        if j > len(curdir) or k < j:
            self.report({'ERROR'}, "Could not deduce game folder name.")
            return{'FINISHED'}

        
        # hl2
        gamedirname = curdir[j:k]
        # root/game
        gamedir = os.path.join(curdir[:i], 'game')

        # root/game/bin
        context.scene.vs.engine_path = os.path.join(gamedir, 'bin')

        # root/game/hl2
        context.scene.vs.game_path = os.path.join(gamedir, gamedirname)

        i = curdir.find('models')
        j = i + curdir[i:].replace('\\', '/').find('/') + 1
        
        modelpath = os.path.dirname(curdir[j:])
        modelname = os.path.basename(bpy.data.filepath).replace('.blend', '.mdl')

        context.scene.qcgen.modelname = os.path.join(modelpath, modelname)
        context.scene.qcgen.cdmaterials = os.path.join('models', modelpath)


        return{'FINISHED'}

class QC_PT_QCPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "QC Generator"
    bl_idname = "QC_PT_QCPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        qcgen = context.scene.qcgen

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False


        if context.scene.vs:
            layout.operator("qcgen.autofill_vs", text="Find Engine Path")

        layout.separator()

        layout.prop(qcgen, "modelname")
        layout.prop(qcgen, "cdmaterials")
        row = layout.row()
        row.template_list("QC_UL_BodyList", "", qcgen,
                             "bodies", qcgen, "bodies_active")
        row = layout.row()
        row.operator("bodies.add", icon='ADD', text="Add")
        row.operator("bodies.remove", icon='REMOVE', text="Remove")
        row.operator('bodies.move_item', icon='TRIA_UP', text='').direction = 'UP'
        row.operator('bodies.move_item', icon='TRIA_DOWN', text='').direction = 'DOWN'

        if qcgen.bodies_active >= 0 and qcgen.bodies:
            item = qcgen.bodies[qcgen.bodies_active]
            #box = layout.box()
            box = layout
            row = box.row()
            row.use_property_split = False
            row.prop(item, "component_type", expand=True)

            if item.component_type != 'collisionmodel': # collision models don't have names
                box.prop(item, "name")

            if item.component_type == 'attachment':
                box.prop(item, "bone")
            else:
                box.prop(item, "path")

            if item.component_type == 'collisionmodel':
                box.prop(item, "mass")

        layout.separator()

        layout.prop(qcgen, "surfaceprop")
        layout.prop(qcgen, "contents")

        split = layout.split()
        col = split.column()
        col.prop(qcgen, "staticprop")
        col = split.column()
        col.prop(qcgen, "scale")

        layout.separator()

        layout.operator("qcgen.write", text="Write QC")

from .vmt_generator import VMT_Properties, classes_vmt

classes = (    
    QC_Body,
    QC_Properties,

    QC_UL_BodyList,
    QC_OT_AddBody,
    QC_OT_RemoveBody,
    QC_OT_MoveBody,

    QC_OT_WriteQC,

    QC_OT_AutofillVS,

    QC_PT_QCPanel
) + classes_vmt


def register():
    from bpy.utils import register_class
    for cl in classes:
        register_class(cl)
    
    def make_pointer(prop_type, nombre="QC Generator"):
        return PointerProperty(name=nombre, type=prop_type)

    bpy.types.Scene.qcgen = make_pointer(QC_Properties)
    bpy.types.Scene.vmtgen = make_pointer(VMT_Properties)


def unregister():
    from bpy.utils import unregister_class
    for cl in classes:
        unregister_class(cl)


if __name__ == "__main__":
    register()
