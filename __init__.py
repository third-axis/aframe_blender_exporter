'''
AFRAME Exporter for Blender
Copyright (c) 2020 Alessandro Schillaci

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
'''

'''
In collaboration with Andrea Rotondo, VR Expert since 1998
informations and contacs:
http://virtual-art.it - rotondo.andrea@gmail.com
https://www.facebook.com/wox76
https://www.facebook.com/groups/134106979989778/
'''

'''
USAGE:
    - create new Blender project
    - install this addon
    - add a right managed CUSTOM PROPERTY
    - open the addon and set your configuration
    - click on "Export A-Frame Project" button
    - your project will be saved in the export directory
    - launch "live-server" (install it with "npm install -g live-server") or "python -m SimpleHTTPServer"

AVAILABLE CUSTOM_PROPERTIES:
    - AFRAME_CUBEMAP: if present, set reflections on to the mesh object (metal -> 1, rough -> 0)
    - AFRAME_ANIMATION:  aframe animation tag. Samples:
        - property: rotation; to: 0 360 0; loop: true; dur: 10000;
        - property: position; to: 1 8 -10; dur: 2000; easing: linear; loop: true;
    - AFRAME_HTTP_LINK: html link when click on object       
    - AFRAME_VIDEO: target=mp4 video to show
    - AFRAME_IMAGES: click to swap images e.g: {"1": "image1.jpg", "2": "image2.jpg"}
    - AFRAME_SHOW_HIDE_OBJECT: click to show or hide another 3d object

THIRD PARTY SOFTWARE:
    This Addon Uses the following 3rdParty software (or their integration/modification):
    - Aframe Joystick - https://github.com/mrturck/aframe-joystick
    - Aframe Components - https://github.com/colinfizgig/aframe_Components
    - Icons - https://ionicons.com/
'''


bl_info = {
    "name" : "Import-Export: Aframe Asset Exporter",
    "author" : "Kitae Kim, Alessandro Schillaci",
    "description" : "Blender Exporter to AFrame WebVR application",
    "blender" : (2, 83, 0),
    "version" : (0, 0, 1),
    "location" : "View3D",
    "warning" : "",
    "category" : "3D View"
}

import os
import bpy
import shutil
import math
from string import Template
import http.server
import urllib.request
import socketserver
import threading
import json

PORT = 8001

# Constants
PATH_INDEX = "templates/models.html"
PATH_ASSETS = "assets/models/"
PATH_ENVIRONMENT = "assets/cubemaps/"
PATH_LIGHTMAPS = "assets/lightmaps/"
PATH_JAVASCRIPT = "js/"


assets = []
entities = []
lights = []
showstats = ""


# Assets html a-frame template
def default_template():
    if not bpy.data.texts.get('models.html'):
        tpl = bpy.data.texts.new('models.html')
        tpl.from_string('''<a-assets>${asset}</a-assets><a-entity>${entity}</a-entity>''')


class AframeExportPanel_PT_Panel(bpy.types.Panel):
    bl_idname = "AFRAME_EXPORT_PT_Panel"
    bl_label = "Aframe Exporter (v 0.0.1)"
    bl_category = "Aframe"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, content):
        scene = content.scene
        layout = self.layout
        layout.use_property_split=True
        layout.use_property_decorate = False

        row = layout.row(align=True)        
        row.prop(scene, 'b_settings', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_settings') else "TRIA_RIGHT", icon_only=False, emboss=False)
        row.label(text="A-Frame", icon='NONE')
        if scene.b_settings:
             row = layout.row(align=True)
             box = row.box()
             box.prop(scene, "b_cubemap")             
             box.prop(scene, "b_cubemap_background")
             box.prop(scene, "s_cubemap_path")
             box.prop(scene, "s_cubemap_ext")      
             box.separator()
        row = layout.row(align=True) 
        row = layout.row(align=True)      
        if scene.b_interactive:     
            row = layout.row(align=True)           
            box.operator("aframe.cubemap")

        row.prop(scene, 'b_bake_lightmap', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_bake_lightmap') else "TRIA_RIGHT", icon_only=False, emboss=False)
        row.label(text="Create Lightmaps", icon='NONE')
        if scene.b_bake_lightmap:
            row = layout.row(align=True)   
            box = row.box()
            #box.separator()            
            box.label(text="Enable github.com/Naxela/The_Lightmapper", icon='NONE')
            box.prop(scene, "b_use_lightmapper")
            box.prop(scene, "f_lightMapIntensity")
            box.operator('aframe.delete_lightmap', text='0 Delete All lightmaps')        
            box.operator('aframe.prepare', text='1 Prepare Selection for Lightmapper')
            box.operator('aframe.bake', text='2 Bake with Lightmapper')
            box.operator('aframe.savelm', text='3 Save Lightmaps')   
            box.operator('aframe.clean', text='4 Clean Lightmaps')            
            #box.separator()         
        row = layout.row(align=True)  
        
        row.prop(scene, 'b_export', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_export') else "TRIA_RIGHT", icon_only=False, emboss=False)
        row.label(text="Exporter", icon='NONE')
        if scene.b_export:
            row = layout.row(align=True)   
            box = row.box()            
            box.prop(scene, "s_project_name")
            box.prop(scene, "export_path")
        #     box.operator('aframe.clear_asset_dir', text='Clear Assets Directory')

        row = layout.row(align=True)       
        row = layout.row(align=True) 
        row.operator('aframe.export', text='Export Assets')



class AframeClean_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.clean"
    bl_label = "Clean"
    bl_description = "Clean"
        
    def execute(self, content):
        # TODO checkout is add-on is present
        bpy.ops.tlm.clean_lightmaps("INVOKE_DEFAULT")
        print("cleaning baked lightmaps")
        return {'FINISHED'}   

class AframeBake_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.bake"
    bl_label = "Bake"
    bl_description = "Bake"
        
    def execute(self, content):
        # TODO checkout is add-on is present
        bpy.ops.tlm.build_lightmaps("INVOKE_DEFAULT")
        print("internal bake")
        return {'FINISHED'}        

class AframeClearAsset_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.clear_asset_dir"
    bl_label = "Clear Asset Directory"
    bl_description = "Clear Asset Directory"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )

        # Clear existing "assests" directory
        assets_dir = os.path.join ( DEST_RES, PATH_ASSETS )
        if os.path.exists( assets_dir ):
            shutil.rmtree( assets_dir )
        return {'FINISHED'}

class AframePrepare_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.prepare"
    bl_label = "Prepare for Ligthmapper"
    bl_description = "Prepare Lightmapper"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        bpy.context.scene.TLM_SceneProperties.tlm_mode = 'GPU'
        view_layer = bpy.context.view_layer
        obj_active = view_layer.objects.active
        selection = bpy.context.selected_objects

        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = obj_active
        for obj in selection:
            obj.select_set(True)
            # some exporters only use the active object
            view_layer.objects.active = obj
            bpy.context.object.TLM_ObjectProperties.tlm_mesh_lightmap_use = True
            bpy.context.object.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = '512'
        
        return {'FINISHED'}

class AframeClear_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.delete_lightmap"
    bl_label = "Delete generated lightmaps"
    bl_description = "Delete Lightmaps"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        
        # delete all _baked textures
        images = bpy.data.images
        for img in images:
            if "_baked" in img.name:
                print("[CLEAR] delete image "+img.name)
                bpy.data.images.remove(img)
        
        #for material in bpy.data.materials:
        #    material.user_clear()
        #    bpy.data.materials.remove(material)
        
        for filename in os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS)):
            os.remove(os.path.join ( DEST_RES, PATH_LIGHTMAPS) + filename)
        
        #if os.path.exists(os.path.join(DEST_RES, PATH_LIGHTMAPS)):
        #    shutil.rmtree(os.path.join(DEST_RES,PATH_LIGHTMAPS))
        #bpy.ops.tlm.build_lightmaps()

        return {'FINISHED'}

class AframeSavelm_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.savelm"
    bl_label = "Save lightmaps"
    bl_description = "Save Lightmaps"
    
    def execute(self, content):
        images = bpy.data.images
        scene = content.scene
        original_format = scene.render.image_settings.file_format
        settings = scene.render.image_settings
        settings.file_format = 'PNG'
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        for img in images:
            if "_baked" in img.name and img.has_data:
                ext = ".png"
     
                img.file_format = 'PNG'
                img.save_render(os.path.join ( DEST_RES, PATH_LIGHTMAPS, img.name+ext ) )
                print("[SAVE LIGHTMAPS] Save image "+img.name)
        settings.file_format = original_format
        return {'FINISHED'}
    
class AframeLoadlm_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.loadlm"
    bl_label = "load lightmaps"
    bl_description = "Load Lightmaps"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        
        # delete all _baked textures
        images = bpy.data.images
        for img in images:
            if "_baked" in img.name:
                print("delete: "+img.name)
                bpy.data.images.remove(img)
                
        for filename in os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS)):
            bpy.data.images.load(os.path.join ( DEST_RES, PATH_LIGHTMAPS) + filename)
        return {'FINISHED'}    
        

class AframeExport_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.export"
    bl_label = "Export to Aframe Project"
    bl_description = "Export AFrame Assets"

    def execute(self, content):
        assets = []
        entities = []
        lights = []
        print("[AFRAME EXPORTER] Exporting project...")
        scene = content.scene
        scene.s_output = "exporting..."
        script_file = os.path.realpath(__file__)
        #print("script_file dir = "+script_file)
        directory = os.path.dirname(script_file)

        # Destination base path
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )


        if __name__ == "__main__":
            #print("inside blend file")
            #print(os.path.dirname(directory))
            directory = os.path.dirname(directory)

        print("[AFRAME EXPORTER] Target Dir = "+directory)

        ALL_PATHS = [ ".", PATH_ASSETS, PATH_LIGHTMAPS, PATH_ENVIRONMENT ]
        for p in ALL_PATHS:
            dp = os.path.join ( DEST_RES, p )
            print ( "--- DEST [%s] [%s] {%s}" % ( DEST_RES, dp, p ) )
            os.makedirs ( dp, exist_ok=True )

        #check if addon or script for correct path
        _resources = [
                        
             [ PATH_JAVASCRIPT, "webxr.js", True ],
             [ PATH_JAVASCRIPT, "camera-cube-env.js", True ],
             [ PATH_ENVIRONMENT, "negx.jpg", True ],
             [ PATH_ENVIRONMENT, "negy.jpg", True ],
             [ PATH_ENVIRONMENT, "negz.jpg", True ],
             [ PATH_ENVIRONMENT, "posx.jpg", True ],
             [ PATH_ENVIRONMENT, "posy.jpg", True ],
             [ PATH_ENVIRONMENT, "posz.jpg", True ],
         ]

     
        # Loop 3D entities
        exclusion_obj_types = ['CAMERA','LAMP','ARMATURE']
        exported_obj = 0
        videocount=0
        imagecount=0
        scalefactor = 2
        lightmap_files = os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS))
        for file in lightmap_files:
            print("[LIGHTMAP] Found Lightmap file: "+file)

        for obj in bpy.data.objects:
            if obj.type not in exclusion_obj_types:
                print("[AFRAME EXPORTER] loop object "+ obj.name)
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(state=True)
                bpy.context.view_layer.objects.active = obj
                #bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
                location = obj.location.copy()
                rotation = obj.rotation_euler.copy()
                
                bpy.ops.object.location_clear()
                actualposition = str(location.x)+" "+str(location.z)+" "+str(-location.y)
                actualscale = str(scalefactor*bpy.data.objects[obj.name].scale.x)+" "+str(scalefactor*bpy.data.objects[obj.name].scale.y)+" "+str(scalefactor*bpy.data.objects[obj.name].scale.z)
            
                actualrotation = "0 "+str(math.degrees(rotation.z))+" 0"    
                    
                # custom aframe code read from CUSTOM PROPERTIES
                reflections = ""
                animation = ""
                link = ""
                baked = ""
                custom = ""
                toggle = ""
                video = False
                image = False
                tag = "entity"
                gltf_model = 'gltf-model="#'+obj.name+'"' 

                # export gltf
                print(obj.type)
                if obj.type == 'MESH' or obj.type == 'EMPTY':
                    if obj.type == 'EMPTY':
                        gltf_model = ''
                    #print(obj.name,"custom properties:")
                    for K in obj.keys():
                        if K not in '_RNA_UI':
                            #print( "\n", K , "-" , obj[K], "\n" )
                            if K == "AFRAME_CUBEMAP" and scene.b_cubemap:
                                if scene.b_camera_cube:
                                    reflections = ' geometry="" camera-cube-env="distance: 500; resolution: 512; repeat: true; interval: 400" '
                                else:
                                    reflections = ' geometry="" cube-env-map="path: '+scene.s_cubemap_path+'; extension: '+scene.s_cubemap_ext+'; reflectivity: 0.99;" '
                    
                        # check if baked texture is present on filesystem
                        #images = bpy.data.images
                        #for img in images:
                        #    if obj.name+"_baked" in img.name and img.has_data:
                        #       print("ok")
                        #       baked = 'light-map-geometry="path: lightmaps/'+img.name+'"'
                        print("[LIGHTMAP] Searching Lightmap for object ["+obj.name+"_baked"+"]")                        
                        for file in lightmap_files:
                            if obj.name+"_baked" in file:
                                print("[LIGHTMAP] Found lightmap: "+file)
                                baked = 'light-map-geometry="path: lightmaps/'+file+'; intensity: '+str(scene.f_lightMapIntensity)+'"'
                            
                        filename = os.path.join ( DEST_RES, PATH_ASSETS, obj.name ) # + '.glft' )
                        bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True)
                        assets.append('\n\t\t\t\t<a-asset-item id="'+obj.name+'" src="./assets/'+obj.name + '.gltf'+'"></a-asset-item>')
                        if scene.b_cast_shadows:
                            entities.append('\n\t\t\t<a-'+tag+' id="#'+obj.name+'" '+gltf_model+' scale="1 1 1" position="'+actualposition+'" visible="true" shadow="cast: true" '+reflections+animation+link+custom+toggle+'></a-'+tag+'>')
                        else:
                            entities.append('\n\t\t\t<a-'+tag+' id="#'+obj.name+'" '+gltf_model+' '+baked+' scale="1 1 1" position="'+actualposition+'" visible="true" shadow="cast: false" '+reflections+animation+link+custom+toggle+'></a-'+tag+'>')
                # deselect object
                obj.location = location
                obj.select_set(state=False)
                exported_obj+=1

        bpy.ops.object.select_all(action='DESELECT')

        # Templating ------------------------------
        #print(assets)
        all_assets = ""
        for x in assets:
            all_assets += x

        all_entities = ""
        for y in entities:
            all_entities += y

        # scene
        if scene.b_stats:
            showstats = "stats"
        else:
            showstats = ""

        #shadows
        if scene.b_cast_shadows:
            showcast_shadows = "true"
            template_render_shadows = 'shadow="type: pcfsoft; autoUpdate: true;"'            
        else:
            showcast_shadows = "false"
            template_render_shadows = 'shadow="type: basic; autoUpdate: false;"'            

        # Sky
        if scene.b_show_env_sky:
            show_env_sky = '<a-sky src="#sky" material="" geometry="" rotation="0 90 0"></a-sky>'                              
        else:
            show_env_sky = '<a-sky color="#ECECEC"></a-sky>'

        # if use bake, the light should have intensity near zero
        if scene.b_use_lightmapper:
            light_directional_intensity = "0"
            light_ambient_intensity = "0.1"
        else:
            light_directional_intensity = "1.0"
            light_ambient_intensity = "1.0"

        #Renderer
        showrenderer = 'renderer="antialias: '+str(scene.b_aa).lower()+'; colorManagement: '+str(scene.b_colorManagement).lower()+'; physicallyCorrectLights: '+str(scene.b_physicallyCorrectLights).lower()+';"'

        default_template()
        t = Template( bpy.data.texts['models.html'].as_string() )
        s = t.substitute(
            asset=all_assets,
            entity=all_entities,
            stats=showstats,
            aframe_version=scene.s_aframe_version,
            cast_shadows=showcast_shadows,
            player_height=scene.f_player_height,
            player_speed=scene.f_player_speed,
            sky=show_env_sky,
            directional_intensity=light_directional_intensity,
            ambient_intensity=light_ambient_intensity,
            render_shadows=template_render_shadows,
            renderer=showrenderer)


        #print(s)

        # Saving the main INDEX FILE
        with open( os.path.join ( DEST_RES, PATH_INDEX ), "w") as file:
            file.write(s)

        scene.s_output = str(exported_obj)+" meshes exported"
        #self.report({'INFO'}, str(exported_obj)+" meshes exported")
        return {'FINISHED'}


# ------------------------------------------- REGISTER / UNREGISTER
_props = [
    ("bool", "b_cubemap", "Cube Env Map", "Enable Cube Map component" ),
    ("str", "s_cubemap_path", "Path", "Cube Env Path", "/env/" ),
    ("bool", "b_cubemap_background", "Enable Background", "Enable Cube Map Background" ),
    ("str", "s_cubemap_ext", "Ext", "Image file extension", "jpg" ),
    ("bool", "b_lightmaps", "Use Lightmaps as Occlusion (GlTF Settings)", "GLTF Models don\'t have lightmaps: turn on this option will save lightmaps to Ambient Occlusion in the GLTF models" ),
    ("str", "export_path", "Export To","Path to the folder 'src'", "C:/Temp/", 'FILE_PATH'),
    ("str", "s_project_name", "Name", "Project's name","aframe-prj"),
    ("str", "s_output", "output","output export","output"),
    ("bool", "b_use_lightmapper", "Use Lightmapper Add-on","Use Lightmapper for baking" ),
    ("bool", "b_camera_cube", "Camera Cube Env","Enable Camera Cube Env component"),
    ("bool", "b_show_env_sky", "Show Environment Sky","Show Environment Sky"),
    ("bool", "b_export", "Exporter settings","b_export"),    
    ("bool", "b_bake", "Bake settings","b_bake"),         
    ("bool", "b_bake_lightmap", "Bake settings","b_bake_lightmap"),     
    ("float", "f_lightMapIntensity", "LightMap Intensity","LightMap Intensity", 2.0),         
]

# CUSTOM PROPERTY OPERATORS
class ShowHideObject(bpy.types.Operator):
    bl_idname = 'aframe.show_hide_object'
    bl_label = 'Add Show Hide Object'
    bl_description = 'Show and Hide object by clicking this entity'
    def execute(self, context):
        try:
            scene = context.scene
            bpy.context.active_object["AFRAME_SHOW_HIDE_OBJECT"] = scene.s_showhide_object
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}
    
class ToogleObjects(bpy.types.Operator):
    bl_idname = 'aframe.toggle_object'
    bl_label = 'Add Toggle Object'
    bl_description = 'Add two toggle objects for selected object'
    def execute(self, context):
        try:
            bpy.context.active_object["AFRAME_TOOGLE_OBJECT"] = '{"1": "id1", "2": "id2"}'
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}
    
class Images(bpy.types.Operator):
    bl_idname = 'aframe.images'
    bl_label = 'Add Toggle Images'
    bl_description = 'Add two toggle images for selected object'
    def execute(self, context):
        try:
            bpy.context.active_object["AFRAME_IMAGES"] = '{"1": "image1.png", "2": "image2.png"}'
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}

class Cubemap(bpy.types.Operator):
    bl_idname = 'aframe.cubemap'
    bl_label = 'Add Cubemap'
    bl_description = 'Add a cubemap for selected object to make it transparent'
    def execute(self, context):
        try:
           bpy.context.active_object["AFRAME_CUBEMAP"] = "1"
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}

class Rotation360(bpy.types.Operator):
    bl_idname = 'aframe.rotation360'
    bl_label = 'Add Rotation on Z'
    bl_description = 'Rotation Object 360 on Z axis'
    def execute(self, context):
        try:
           bpy.context.active_object["AFRAME_ANIMATION"] = "property: rotation; to: 0 360 0; loop: true; dur: 10000"
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}

class LinkUrl(bpy.types.Operator):
    bl_idname = 'aframe.linkurl'
    bl_label = 'Add Link Web'
    bl_description = 'Insert URL WEB'
    def execute(self, context):
        try:
            scene = context.scene
            bpy.context.active_object["AFRAME_HTTP_LINK"] = scene.s_link
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}

class VideoPlay(bpy.types.Operator):
    bl_idname = 'aframe.videoplay'
    bl_label = 'Add Video'
    bl_description = 'Insert Video'
    def execute(self, context):
        try:
            scene = context.scene
            bpy.context.active_object["AFRAME_VIDEO"] = scene.s_video
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}


def _reg_bool ( scene, prop, name, descr, default = False ):
    setattr ( scene, prop, bpy.props.BoolProperty ( name = name, description = descr, default = default ) )

def _reg_str ( scene, prop, name, descr, default = "", subtype = "" ):
    if subtype:
        setattr ( scene, prop, bpy.props.StringProperty ( name = name, description = descr, default = default, subtype = subtype ) )
    else:
        setattr ( scene, prop, bpy.props.StringProperty ( name = name, description = descr, default = default ) )


def _reg_float ( scene, prop, name, descr, default = 0.0 ):
    setattr ( scene, prop, bpy.props.FloatProperty ( name = name, description = descr, default = default ) )

def register():
    scn = bpy.types.Scene

    bpy.utils.register_class(AframeExportPanel_PT_Panel)
    bpy.utils.register_class(AframeBake_OT_Operator)
    bpy.utils.register_class(AframeClean_OT_Operator)
    bpy.utils.register_class(AframeExport_OT_Operator)
    bpy.utils.register_class(AframeServe_OT_Operator)
    bpy.utils.register_class(AframeSavelm_OT_Operator)
    bpy.utils.register_class(AframeClear_OT_Operator)
    bpy.utils.register_class(AframePrepare_OT_Operator)
    bpy.utils.register_class(AframeClearAsset_OT_Operator)    
    bpy.utils.register_class(Rotation360)
    bpy.utils.register_class(LinkUrl)
    bpy.utils.register_class(VideoPlay)
    bpy.utils.register_class(Cubemap)
    bpy.utils.register_class(Images)       
    bpy.utils.register_class(ToogleObjects)       
    bpy.utils.register_class(ShowHideObject)                   
    
    for p in _props:
        if p [ 0 ] == 'str': _reg_str ( scn, * p [ 1 : ] )
        if p [ 0 ] == 'bool': _reg_bool ( scn, * p [ 1 : ] )
        if p [ 0 ] == 'float': _reg_float ( scn, * p [ 1 : ] )

def unregister():
    bpy.utils.unregister_class(AframeExportPanel_PT_Panel)
    bpy.utils.unregister_class(AframeBake_OT_Operator)
    bpy.utils.unregister_class(AframeClean_OT_Operator)    
    bpy.utils.unregister_class(AframeExport_OT_Operator)
    bpy.utils.unregister_class(AframeServe_OT_Operator)
    bpy.utils.unregister_class(AframeSavelm_OT_Operator)
    bpy.utils.unregister_class(AframeClear_OT_Operator)
    bpy.utils.unregister_class(AframePrepare_OT_Operator)
    bpy.utils.unregister_class(AframeClearAsset_OT_Operator)    
    bpy.utils.unregister_class(Rotation360)
    bpy.utils.unregister_class(LinkUrl)
    bpy.utils.unregister_class(VideoPlay)
    bpy.utils.unregister_class(Cubemap)
    bpy.utils.unregister_class(Images)
    bpy.utils.unregister_class(ToogleObjects)    
    bpy.utils.unregister_class(ShowHideObject)      

    for p in _props:
        del bpy.types.Scene [ p [ 1 ] ]

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
