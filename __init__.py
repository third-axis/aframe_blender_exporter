'''
Originally
AFRAME Exporter for Blender
Copyright (c) 2020 Alessandro Schillaci

Adapted by Kitae Kim, 2021 to be a simpler asset exporter from Blender to Aframe.

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
'''

bl_info = {
    "name" : "Import-Export: Aframe Asset Exporter",
    "author" : "Kitae Kim, Alessandro Schillaci",
    "description" : "Blender Exporter to AFrame WebXR",
    "blender" : (2, 93, 3),
    "version" : (0, 0, 8),
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
PATH_INDEX = "templates/blender.html"
PATH_ASSETS = "assets/models/"
PATH_ENVIRONMENT = "assets/cubemap/"
PATH_LIGHTMAPS = "assets/lightmaps/"
PATH_JAVASCRIPT = "js/"

assets = []
entities = []
lights = []
showstats = ""

# Need to subclass SimpleHTTPRequestHandler so we can serve cache-busting headers
class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_my_headers()
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def send_my_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

class Server(threading.Thread):
    instance = None
    folder = ""
    should_stop = False
        
    def set_folder(self, folder):
        self.folder = folder
        
    def run(self):
        Handler = MyHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            os.chdir(self.folder)
            while True:
                if self.should_stop:
                    httpd.server_close()
                    break
                httpd.handle_request()

    def stop(self):
        self.should_stop = True
        # Consume the last handle_request call that's still pending
        with urllib.request.urlopen(f'http://localhost:{PORT}/') as response:
            html = response.read()


######    Blender Assets html A-frame template    ######-------------------------------------------------------------------------------------------------
def default_template():
    if not bpy.data.texts.get('blender.html'):
        tpl = bpy.data.texts.new('blender.html')
        tpl.from_string('''${asset}${entity}''')


class AframeExportPanel_PT_Panel(bpy.types.Panel):
    bl_idname = "AFRAME_EXPORT_PT_Panel"
    bl_label = "Aframe Exporter (v 0.0.8)"
    bl_category = "Aframe"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, content):
        scene = content.scene
        layout = self.layout
        layout.use_property_split=True
        layout.use_property_decorate = False
        #col = layout.column(align=False)
        #col = layout.column(align=True)
        #row = col.row()
        #col.label(text="Exporter Settings", icon='NONE')
        row = layout.row(align=True)        
        row.prop(scene, 'b_settings', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_settings') else "TRIA_RIGHT", icon_only=False, emboss=False)
        row.label(text="A-Frame", icon='NONE')
        if scene.b_settings:
             row = layout.row(align=True)
             box = row.box()
            #box.prop(scene, "s_aframe_version")
            #box.prop(scene, "b_stats")
            #box.prop(scene, "b_joystick")
            #box.prop(scene, "b_vr_controllers")
            #col.prop(scene, "b_hands")
             box.prop(scene, "b_cubemap")
             box.prop(scene, "b_camera_cube")
        #     box.prop(scene, "b_show_env_sky")                  
        #     box.prop(scene, "b_cubemap_background")
             box.prop(scene, "s_cubemap_path")
             box.prop(scene, "s_cubemap_ext")
             box.operator("aframe.cubemap")    
        #     #col.prop(scene, "b_blender_lights")
        #     box.prop(scene, "b_cast_shadows")
             box.separator()
        row = layout.row(align=True) 
        # row.prop(scene, 'b_renderer', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_renderer') else "TRIA_RIGHT", icon_only=False, emboss=False)
        # row.label(text="Renderer", icon='NONE')
        # if scene.b_renderer:     
        #     row = layout.row(align=True)           
        #     box = row.box()
        #     box.prop(scene, "b_aa")
        #     box.prop(scene, "b_colorManagement")       
        #     box.prop(scene, "b_physicallyCorrectLights")                                    
        #     box.separator()
        # row = layout.row(align=True)         
        # row.prop(scene, 'b_player', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_player') else "TRIA_RIGHT", icon_only=False, emboss=False)
        # row.label(text="Player", icon='NONE')
        # if scene.b_player:     
        #     row = layout.row(align=True)           
        #     box = row.box()
            #box.prop(scene, "b_raycast")
            #box.prop(scene, "f_raycast_length")
            #box.prop(scene, "f_raycast_interval")
            #box.prop(scene, "f_player_height")
            #box.prop(scene, "f_player_speed")
            #box.separator()
        # row = layout.row(align=True)      
        # #row.prop(scene, 'b_interactive', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_interactive') else "TRIA_RIGHT", icon_only=False, emboss=False)
        # row.label(text="Interactive / Action", icon='NONE')
        # if scene.b_interactive:     
        #     row = layout.row(align=True)           
        #     box = row.box()
        #     box.label(text="Add interactive or action to selected", icon='NONE')  
        #     box.operator("aframe.cubemap")
        #     box.operator("aframe.rotation360")
        #     box.operator("aframe.images")
        
        #     row = box.column_flow(columns=2, align=False)
        #     row.operator("aframe.show_hide_object")
        #     row.prop(scene, "s_showhide_object", text="")

        #     row = box.column_flow(columns=2, align=False)
        #     row.operator("aframe.toggle_object")
        #     row.prop(scene, "s_toggle_object", text="")            
            
        #     row = box.column_flow(columns=2, align=False)
        #     row.operator("aframe.linkurl")
        #     row.prop(scene, "s_link", text="")
            
        #     row = box.column_flow(columns=2, align=False)
        #     row.operator("aframe.videoplay")
        #     row.prop(scene, "s_video", text="")
        # row = layout.row(align=True)      

        # row.prop(scene, 'b_bake', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_bake') else "TRIA_RIGHT", icon_only=False, emboss=False)
        # row.label(text="Bake", icon='NONE')
        # if scene.b_bake:
        #     row = layout.row(align=True)   
        #     box = row.box()
        #     #box.separator()
        #     box.operator('aframe.delete_lightmap', text='0 Delete All lightmaps')        
        #     box.operator('aframe.prepare', text='1 Prepare Selection for Lightmapper')
        #     box.operator('aframe.bake', text='2 Bake with Lightmapper')
        #     box.operator('aframe.savelm', text='3 Save Lightmaps')   
        #     box.operator('aframe.clean', text='4 Clean Lightmaps')            
        #     #box.separator()         
        # row = layout.row(align=True) 

        row.prop(scene, 'b_bake_lightmap', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_bake_lightmap') else "TRIA_RIGHT", icon_only=False, emboss=False)
        row.label(text="Create Lightmaps", icon='NONE')
        if scene.b_bake_lightmap:
            row = layout.row(align=True)   
            box = row.box()
            #box.separator()            
            box.label(text="Enable github.com/Naxela/The_Lightmapper", icon='NONE')
            box.prop(scene, "b_use_lightmapper")
            box.prop(scene, "f_lightMapIntensity")
            #box.operator('aframe.delete_lightmap', text='0 Delete All lightmaps')        
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
            #box.operator('aframe.clear_asset_dir', text='Clear Assets Directory')

        row = layout.row(align=True)       
        row = layout.row(align=True) 
        row.operator('aframe.export', text='Export Assets')
        # row = layout.row(align=True) 
        # serve_label = "Stop Serving" if Server.instance else "Start Serving"
        # row.operator('aframe.serve', text=serve_label)
        # row = layout.row(align=True) 
        # if Server.instance:
        #     row.operator("wm.url_open", text="Open Preview").url = f'http://localhost:{PORT}'
        #     row = layout.row(align=True) 
        # row.label(text=scene.s_output, icon='INFO')


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
    bl_label = "Prepare for Lightmapper"
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

# class AframeClear_OT_Operator(bpy.types.Operator):
#     bl_idname = "aframe.delete_lightmap"
#     bl_label = "Delete generated lightmaps"
#     bl_description = "Delete Lightmaps"
    
#     def execute(self, content):
#         scene = content.scene
#         DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        
        # delete all _baked textures
        # images = bpy.data.images
        # for img in images:
        #     if "_baked" in img.name:
        #         print("[CLEAR] delete image "+img.name)
        #         bpy.data.images.remove(img)
        
        #for material in bpy.data.materials:
        #    material.user_clear()
        #    bpy.data.materials.remove(material)
        
        # for filename in os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS)):
        #     os.remove(os.path.join ( DEST_RES, PATH_LIGHTMAPS) + filename)
        
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
                #ext = "."+img.file_format
                #img.filepath = image_dir_path+img.name+ext         
                #print( os.path.join ( DEST_RES, PATH_LIGHTMAPS, img.name+ext ) )      
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
        
class AframeServe_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.serve"
    bl_label = "Serve Aframe Preview"
    bl_description = "Serve AFrame"
    
    def execute(self, content):
        if (Server.instance):
            Server.instance.stop()
            Server.instance = None
            return {'FINISHED'}
        scene = content.scene
        Server.instance = Server()
        Server.instance.set_folder(os.path.join ( scene.export_path, scene.s_project_name ))
        Server.instance.start()
        
        return {'FINISHED'}

class AframeExport_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.export"
    bl_label = "Export to Aframe Project"
    bl_description = "Export AFrame"

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
        #PATH_RESOURCES, PATH_MEDIA, PATH_ENVIRONMENT, PATH_JAVASCRIPT,
        for p in ALL_PATHS:
            dp = os.path.join ( DEST_RES, p )
            print ( "--- DEST [%s] [%s] {%s}" % ( DEST_RES, dp, p ) )
            os.makedirs ( dp, exist_ok=True )

        #check if addon or script for correct path
        _resources = [
        #     [ ".", "favicon.ico", True ],
        #     [ ".", "style.css" , True],
        #     [ PATH_RESOURCES, "sky.jpg", False ],
        #     [ PATH_RESOURCES, "play.png", False ],
        #     [ PATH_RESOURCES, "pause.png", False],
        #     [ PATH_RESOURCES, "play-skip-back.png", False],
        #     [ PATH_RESOURCES, "mute.png",False ],
        #     [ PATH_RESOURCES, "volume-low.png",False ],
        #     [ PATH_RESOURCES, "volume-high.png",False ],
        #     [ PATH_MEDIA, "image1.png",False ],
        #     [ PATH_MEDIA, "image2.png",False ],                        
             [ PATH_JAVASCRIPT, "webxr.js", True ],
        #     [ PATH_JAVASCRIPT, "joystick.js", True ],
             [ PATH_JAVASCRIPT, "camera-cube-env.js", True ],
             [ PATH_ENVIRONMENT, "negx.jpg", True ],
             [ PATH_ENVIRONMENT, "negy.jpg", True ],
             [ PATH_ENVIRONMENT, "negz.jpg", True ],
             [ PATH_ENVIRONMENT, "posx.jpg", True ],
             [ PATH_ENVIRONMENT, "posy.jpg", True ],
             [ PATH_ENVIRONMENT, "posz.jpg", True ],
         ]

        # SRC_RES = os.path.join ( directory, PATH_RESOURCES )
        # for dest_path, fname, overwrite in _resources:
        #     if overwrite:
        #         shutil.copyfile ( os.path.join ( SRC_RES, fname ), os.path.join ( DEST_RES, dest_path, fname ) )
        #     else:
        #         if not os.path.exists(os.path.join ( DEST_RES, dest_path, fname )):
        #             shutil.copyfile ( os.path.join ( SRC_RES, fname ), os.path.join ( DEST_RES, dest_path, fname ) )                    

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
                #pi = 22.0/7.0
                #actualrotation = str(((bpy.data.objects[obj.name].rotation_euler.x) / (2 * pi) * 360) - 90) +" " + str(((bpy.data.objects[obj.name].rotation_euler.z) / (2 * pi) * 360)-0) + " " + str(((bpy.data.objects[obj.name].rotation_euler.y) / (2 * pi) * 360)+90)
                #actualrotation = str(bpy.data.objects[obj.name].rotation_euler.x) +" " + str(bpy.data.objects[obj.name].rotation_euler.z)+ " " + str(bpy.data.objects[obj.name].rotation_euler.y)
                #actualrotation = str(math.degrees(-89.99+bpy.data.objects[obj.name].rotation_euler.x)) +" " + str(90+math.degrees(bpy.data.objects[obj.name].rotation_euler.y))+ " " + str(-90+math.degrees(bpy.data.objects[obj.name].rotation_euler.z))
                #actualrotation = str(math.degrees(rotation.x))+" "+str(math.degrees(rotation.z))+" "+str(math.degrees(-rotation.y))    
                actualrotation = "0 "+str(math.degrees(rotation.z))+" 0"    
                    
                # custom aframe code read from CUSTOM PROPERTIES --- This is where the paths are written for the assets and entities html code that is generated in the html file
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
                                    reflections = ' geometry="" cube-env-map="path: ../src/assets/cubemap/; extension: '+scene.s_cubemap_ext+'; reflectivity: 0.99;" '
                            elif K == "AFRAME_ANIMATION":
                                animation = ' animation= "'+obj[K]+'" '
                            elif K == "AFRAME_HTTP_LINK":
                                #link = ' link="href: '+obj[K]+'" class="clickable" '
                                link = ' link-handler="target: '+obj[K]+'" class="clickable" '
                            elif K == "AFRAME_VIDEO":
                                #print("--------------- pos " + actualposition)
                                #print("--------------- rot " + actualrotation)
                                #print("--------------- scale " + actualscale)                                
                                #filename = os.path.join ( DEST_RES, PATH_ASSETS, obj.name ) # + '.glft' )
                                #bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True)
                                #assets.append('\n\t\t\t\t<a-asset-item id="'+obj.name+'" src="./assets/'+obj.name + '.gltf'+'"></a-asset-item>')                                
                                assets.append('\n\t\t\t\t<video id="video_'+str(videocount)+'" loop="true" autoplay="true" src="./media/'+obj[K]+'"></video>')
                                entities.append('\n\t\t\t<a-video id="#v_'+str(videocount)+'" src="#video_'+str(videocount)+'" width="1" height="1" scale="'+actualscale+'" position="'+actualposition+'" rotation="'+actualrotation+'" visible="true" shadow="cast: false" '+animation+link+'></a-video>')
                                #entities.append('\n\t\t\t<a-video id="#v_'+str(videocount)+'" src="#video_'+str(videocount)+'" width="'+str(bpy.data.objects[obj.name].scale.x)+'" height="'+str(bpy.data.objects[obj.name].scale.y)+'" scale="1 1 1" position="'+actualposition+'" rotation="'+actualrotation+'" visible="true" shadow="cast: false" '+animation+link+'></a-video>')
                                #entities.append('\n\t\t\t<a-entity id="#'+obj.name+'" gltf-model="#'+obj.name+'" material="src: #video_'+str(videocount)+'" scale="'+actualscale+'" rotation="'+actualrotation+'" position="'+actualposition+'"></a-entity>')
                                video = True
                                videocount = videocount +1
                            elif K == "AFRAME_IMAGES":
                                #print(".....images")
                                image = True
                                imagecount = imagecount +1
                                #load K
                                #json_images = '{"1": "image1.jpg", "2": "image2.jpg"}'
                                json_images = obj[K]
                                json_dictionary = json.loads(json_images)
                                for key in json_dictionary:
                                    #print(key, ":", json_dictionary[key])
                                    assets.append('\n\t\t\t\t<img id="image_'+key+'" src="./media/'+json_dictionary[key]+'"></img>')
                                entities.append('\n\t\t\t<a-image images-handler id="#i_'+str(imagecount)+'" src="#image_'+key+'" class="clickable" width="1" height="1" scale="'+actualscale+'" position="'+actualposition+'" rotation="'+actualrotation+'" visible="true" shadow="cast: false"></a-image>')
                            elif K == "AFRAME_SHOW_HIDE_OBJECT":
                                toggle = ' toggle-handler="target: #'+obj[K]+';" class="clickable" '
                            elif K == "AFRAME_TAG":
                                tag = obj[K]
                            elif K == "AFRAME_NOGLTF":
                                gltf_model = ""
                            elif K.startswith('AFRAME_'):
                                attr   = K.split("AFRAME_")[1].lower()
                                custom = custom+' '+attr+'="'+str(obj[K])+'"'

                    if video == False and image == False:                        
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
                                baked = 'light-map-geometry="path: ../src/assets/lightmaps/'+file+'; intensity: '+str(scene.f_lightMapIntensity)+'"'
                            
                        filename = os.path.join ( DEST_RES, PATH_ASSETS, obj.name ) # + '.glb' )
                        bpy.ops.export_scene.gltf(filepath=filename, export_format='GLB', use_selection=True, export_image_format='JPEG', export_texture_dir='', export_texcoords=True, export_normals=True, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6, export_draco_position_quantization=14, export_draco_normal_quantization=10, export_draco_texcoord_quantization=12, export_draco_color_quantization=10, export_draco_generic_quantization=12, export_tangents=False, export_materials='EXPORT', export_colors=False, use_mesh_edges=False, use_mesh_vertices=False, export_cameras=False, export_selected=False, use_selection=False, use_visible=True, use_renderable=False, use_active_collection=False, export_extras=False, export_yup=True, export_apply=False, export_animations=True, export_frame_range=True, export_frame_step=1, export_force_sampling=True, export_nla_strips=True, export_def_bones=False, export_current_frame=False, export_skins=True, export_all_influences=False, export_morph=True, export_morph_normal=True, export_morph_tangent=False, export_lights=False, export_displacement=False, will_save_settings=False, filter_glob='*.glb;*.gltf')
                        assets.append('\n\t\t\t\t<a-asset-item id="'+obj.name+'" src="../src/assets/models/'+obj.name + '.glb'+'"></a-asset-item>')
                        if scene.b_cast_shadows:
                            entities.append('\n\t\t\t<a-'+tag+' id="#'+obj.name+'" '+gltf_model+' scale="1 1 1" position="'+actualposition+'" visible="true" shadow="cast: true" shadow="receive: true"'+reflections+animation+link+custom+toggle+'></a-'+tag+'>')
                        else:
                            entities.append('\n\t\t\t<a-'+tag+' id="#'+obj.name+'" '+gltf_model+' '+baked+' scale="1 1 1" position="'+actualposition+'" visible="true" shadow="cast: false" shadow="receive: true"'+reflections+animation+link+custom+toggle+'></a-'+tag+'>')
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

        # # joystick
        # if scene.b_joystick:
        #     showjoystick = "joystick"
        # else:
        #     showjoystick = ""

        # if scene.b_raycast:
        #     raycaster='raycaster = "far: '+str(scene.f_raycast_length)+'; interval: '+str(scene.f_raycast_interval)+'; objects: .clickable,.links"'
        # else:
        #     raycaster=""

        # #vr_controllers
        # if scene.b_vr_controllers:
        #     showvr_controllers = '<a-entity id="leftHand" oculus-touch-controls="hand: left" vive-controls="hand: left"></a-entity>\n\t\t\t\t\t<a-entity id="rightHand" laser-controls oculus-touch-controls="hand: right" vive-controls="hand: right" '+raycaster+'></a-entity>'
        # else:
        #     showvr_controllers = ""

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
        t = Template( bpy.data.texts['blender.html'].as_string() )
        s = t.substitute(
            asset=all_assets,
            entity=all_entities,
            stats=showstats,
            aframe_version=scene.s_aframe_version,
            #joystick=showjoystick,
            #vr_controllers=showvr_controllers,
            cast_shadows=showcast_shadows,
            player_height=scene.f_player_height,
            player_speed=scene.f_player_speed,
            #show_raycast=raycaster,
            sky=show_env_sky,
            directional_intensity=light_directional_intensity,
            ambient_intensity=light_ambient_intensity,
            render_shadows=template_render_shadows,
            renderer=showrenderer)


        #print(s)

        # Saving the main INDEX FILE -------------------------------------------------------------------------------------------------------------------
        with open( os.path.join ( DEST_RES, PATH_INDEX ), "w") as file:
            file.write(s)

        scene.s_output = str(exported_obj)+" meshes exported"
        #self.report({'INFO'}, str(exported_obj)+" meshes exported")
        return {'FINISHED'}


# ------------------------------------------- REGISTER / UNREGISTER
_props = [
    ("str", "s_aframe_version", "A-Frame version", "A-Frame version", "0.0.8" ),
    ("bool", "b_stats", "Show Stats", "Enable rendering stats in game" ),
    ("bool", "b_vr_controllers", "Enable VR Controllers (HTC,Quest)", "Enable HTC/Quest Controllers in game", True ),
    ("bool", "b_hands", "Use Hands Models", "Use hands models instead of controllers", True ),
   # ("bool", "b_joystick", "Show Joystick", "Add a joystick on screen" ),
    ("bool", "b_cubemap", "Cube Env Map", "Enable Cube Map component", True ),
    ("str", "s_cubemap_path", "Path", "Cube Env Path", "/src/assets/cubemap" ),
    ("bool", "b_cubemap_background", "Enable Background", "Enable Cube Map Background", False ),
    ("str", "s_cubemap_ext", "Ext", "Image file extension", "png" ),
    ("bool", "b_blender_lights", "Export Blender Lights", "Export Blender Lights or use Aframe default ones" ),
    ("bool", "b_cast_shadows", "Cast Shadows", "Cast and Receive Shadows" ),
    ("bool", "b_lightmaps", "Use Lightmaps as Occlusion (GlTF Settings)", "GLTF Models don\'t have lightmaps: turn on this option will save lightmaps to Ambient Occlusion in the GLTF models" ),
    ("float", "f_player_speed", "Player Speed", "Player Speed", 0.5 ),
    #("float", "f_raycast_length", "Raycast Length","Raycast lenght to interact with objects", 10.0 ),
    #("float", "f_raycast_interval", "Raycast Interval","Raycast Interval to interact with objects", 1500.0 ),
    ("str", "export_path", "Export To","Path to the folder containing the files to import", "D:/Temp/aframeProject", 'FILE_PATH'),
    ("str", "s_project_name", "Name", "Project's name",""),
    ("str", "s_output", "output","output export","output"),
    ("bool", "b_use_lightmapper", "Use Lightmapper Add-on","Use Lightmapper for baking", True ),
    ("bool", "b_camera_cube", "Camera Cube Env","Enable Camera Cube Env component", False),
    ("float", "f_player_height", "Player Height","Player Height", 1.7),
    #("bool", "b_raycast", "Enable Raycast","Enable Raycast"),
    ("bool", "b_show_env_sky", "Show Environment Sky","Show Environment Sky"),
    ("bool", "b_settings", "A-Frame settings","b_settings"),
    ("bool", "b_player", "Player settings","b_player"),    
    ("bool", "b_interactive", "Interactive","b_interactive"),        
    ("bool", "b_export", "Exporter settings","b_export"),    
    ("bool", "b_bake", "Bake settings","b_bake"),         
    ("bool", "b_bake_lightmap", "Bake settings","b_bake_lightmap"),     
    ("float", "f_lightMapIntensity", "LightMap Intensity","LightMap Intensity", 2.0),     
    ("str", "s_link", "Link Url", "Link Url" , "https://www.google.it/"),    
    ("str", "s_video", "Video File Name", "Video File Name" , "video.mp4"),        
    ("str", "s_showhide_object", "Show Hide Object", "Show Hide Object: insert object id \ne.g. Cube.001" , "Cube.001"),    
    ("str", "s_toggle_object", "Toggle Objects", 'Insert n id objects in JSON format e.g.\n{"1": "Cube.001", "2": "Cube.002"}, "3": "Cube.003"}' , '{"1": "Cube.001", "2": "Cube.002"}'),        
    ("bool", "b_renderer", "Renderer Settings","A-Frame Renderer Settings"),
    ("bool", "b_aa", "Antialiasing","Antialiasing"),    
    ("bool", "b_colorManagement", "Color Management","ColorManagement"),        
    ("bool", "b_physicallyCorrectLights", "Physically Correct Lights","PhysicallyCorrectLights"),         
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
    #bpy.utils.register_class(AframeClear_OT_Operator)
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
