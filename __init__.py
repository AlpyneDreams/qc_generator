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
    "blender": (2, 90, 0),
    "version": (1, 0, 6),
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
    qc_text : PointerProperty(
        name="QC Text Output",
        type=bpy.types.Text,
        options={'HIDDEN'}
    )
    open_in_text_editor: BoolProperty(
        name="Open in Text Editor",
        options={'HIDDEN'},
        default=True
    )
    save_qc_file: BoolProperty(
        name="Automatically Overwrite File",
        options={'HIDDEN'},
        default=True
    )
    
    collisionmodel : PointerProperty(
        name="Collision Model",
        type=bpy.types.Collection,
        options={'HIDDEN'}
    )
    concave: BoolProperty(
        name="Concave",
        options={'HIDDEN'},
        default=False
    )
    use_collisionjoints: BoolProperty(
        name="Collision Joints",
        options={'HIDDEN'}
    )
    generate_bone_followers: BoolProperty(
        name="Generate Bone Followers",
        options={'HIDDEN'},
        default=True
    )
    modelname: StringProperty(
        name="MDL File Path", description="The path of the .mdl file relative to the models/ dir.")
    cdmaterials: StringProperty(
        name="CD Materials", description="The path of the model's materials relative to the materials/ dir.",
        default="models/")
    bodies: CollectionProperty(
        name="Bodies", type=QC_Body)
    bodies_active: IntProperty(
        name="Selected Body", default=0, min=0, options={'HIDDEN'})  # , update=bodies_active_changed)
    staticprop: BoolProperty(
        name="Static Prop", default=False)
    scale: FloatProperty(
        name="Scale",
        default=1
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

# based on biggest_non_image_area
# from source/blender/editors/render/render_view.c
# returns biggest area that is not uv/image editor
# uses properties window as the last possible alternative
def get_biggest_area(context):
    sc = context.screen
    big = None
    maxsize = 0
    pwmaxsize = 0
    foundwin = False
    for sa in sc.areas:
        # only consider areas larger than 30x30
        if sa.width > 30 and sa.height > 30:
            size = sa.width * sa.height
            if sa.type == 'PROPERTIES':
                # only consider PROPERTIES windows if nothing else has been found
                if not foundwin and size > pwmaxsize:
                    bwmaxsize = size
                    big = sa
            elif size > maxsize:
                maxsize = size
                big = sa
                foundwin = True
    return big

class QC_OT_WriteQC(Operator):
    bl_idname = "qcgen.write"
    bl_label = "Write QC File"

    def execute(self, context):
        from .qcfile import write_qc_file, qc_from_vs
        qcgen = context.scene.qcgen
        qcgen.last_info_msg = ""
        qctxt = qc_from_vs(context)

        if not qcgen.qc_text:
            i = len(bpy.data.texts)
            bpy.ops.text.new()
            qcgen.qc_text = bpy.data.texts[i]
            qcgen.qc_text.name = os.path.splitext(os.path.basename(bpy.data.filepath))[0] + ".qc"
        qc_text = qcgen.qc_text
        qc_text.clear()
        qc_text.write(qctxt)
        
        text_editor_area = None

        if qcgen.open_in_text_editor:
            # trying to emulate bpy.ops.render.view_show("INVOKE_DEFAULT")
            # but pop up a text editor instead of an image editor.
            # FIXME: this area should open as a temp area like view_show does
            text_editor = None

            # look for a text editor already on this screen
            for area in bpy.context.screen.areas:
                if area.type == 'TEXT_EDITOR':
                    text_editor = area.spaces.active
                    text_editor_area = area
                    break
            
            # otherwise find the largest area on this screen
            if not text_editor:
                area = get_biggest_area(context)
                if area:
                    area.type = 'TEXT_EDITOR'
                    text_editor = area.spaces.active
                    text_editor_area = area
            
            if text_editor:
                text_editor.text = qc_text

                # scroll to top (FIXME: only works on subsequent uses)
                text_editor.top = 0
                text_editor.show_syntax_highlight = True
                text_editor.show_line_highlight = True
        
        # HACK: currently not able to call bpy.ops.text.save()
        # from this context. we can write the file but it will
        # cause the file to be marked conflicted (even though it's not)
        if qcgen.save_qc_file:
            if qc_text.filepath:
                qc_path = qc_text.filepath
            else:
                qc_path = os.path.splitext(os.path.basename(bpy.data.filepath))[0] + ".qc"
                qc_path = os.path.join(os.path.dirname(bpy.data.filepath), qc_path)
                qc_text.filepath = qc_path
            with open(qc_path, 'w', encoding='utf8') as f:
                f.write(qc_text.as_string())
            
            self.report({'INFO'}, "Saved file " + os.path.basename(qc_path))
        
        return{'FINISHED'}

class QC_OT_AutofillVS(Operator):
    """Automatically determine paths for Source Engine Export"""
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

        if not context.scene.vs.export_path:
            context.scene.vs.export_path = "//"

        i = curdir.find('models')
        j = i + curdir[i:].replace('\\', '/').find('/') + 1
        
        modelpath = os.path.dirname(curdir[j:])
        modelname = os.path.basename(bpy.data.filepath).replace('.blend', '.mdl')

        context.scene.qcgen.modelname = os.path.join(modelpath, modelname)
        context.scene.qcgen.cdmaterials = os.path.join('models', modelpath)


        return{'FINISHED'}

class BasePanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    #bl_options = {"DEFAULT_CLOSED"}
    bl_context = "scene"
    qc_icon = None

    def draw_header(self, context):
        if self.qc_icon:
            self.layout.label(icon=self.qc_icon)	

    def draw(self, context):
        qcgen = context.scene.qcgen
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True
        self.paint(qcgen, layout, context)

    def paint(self, qcgen, layout: bpy.types.UILayout, context: bpy.types.Context):
        pass

class QC_PT_QCPanel(BasePanel, bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "QC Generator"
    bl_idname = "QC_PT_QCPanel"

    def paint(self, qcgen, layout, context):
        layout.use_property_split = False

        if context.scene.vs:
            layout.operator("qcgen.autofill_vs", text="Find Engine Path")

        layout.operator("qcgen.write", text="Write QC")

class QC_PT_Paths(BasePanel, bpy.types.Panel):
    bl_parent_id = "QC_PT_QCPanel"
    bl_label = "Paths"
    qc_icon = 'FILE_FOLDER'

    def paint(self, qcgen, layout, context):
        layout.use_property_split = False
        
        layout.prop(qcgen, "modelname")
        layout.prop(qcgen, "cdmaterials")

        layout.use_property_split = True

class QT_PT_QCOutput(BasePanel, bpy.types.Panel):
    bl_parent_id = "QC_PT_QCPanel"
    bl_label = "Output"
    qc_icon = 'TEXT'

    def paint(self, qcgen, layout, context):
        layout.prop(qcgen, 'qc_text')

        layout.prop(qcgen, 'open_in_text_editor')
        layout.prop(qcgen, 'save_qc_file')

class QT_PT_QCModel(BasePanel, bpy.types.Panel):
    bl_parent_id = "QC_PT_QCPanel"
    bl_label = "Model"
    qc_icon = 'MESH_UVSPHERE'

    def paint(self, qcgen, layout, context):
        layout.prop(qcgen, "staticprop")
        layout.prop(qcgen, "scale")

class QT_PT_QCPhysics(BasePanel, bpy.types.Panel):
    bl_parent_id = "QC_PT_QCPanel"
    bl_label = "Physics"
    qc_icon = 'MESH_ICOSPHERE'

    def paint(self, qcgen, layout, context):
        layout.prop(qcgen, 'collisionmodel')        

        row = layout.row()
        if qcgen.collisionmodel:
            row.enabled = True
        else:
            row.enabled = False
        layout.prop(qcgen, 'concave')
        layout.prop(qcgen, 'use_collisionjoints')

        col = layout.column()
        col.enabled = qcgen.use_collisionjoints
        col.prop(qcgen, 'generate_bone_followers')

        #layout.prop(qcgen, "contents")

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

    QC_PT_QCPanel,
    QC_PT_Paths,
    QT_PT_QCOutput,
    QT_PT_QCModel,
    QT_PT_QCPhysics,
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
