
# Important notes:
#
# 1. You should type the correct Orbiter path. Otherwise, the script won't open the textures. 
#  You can set ORBITER_PATH_DEFAULT variable here at the beginning, and then re-register the add-on.
#
# 2. The script doesn't import vertex normals. It seems that Blender often recalculates vertex normals, so it's useless to import them.
#
# 3. Blender uses right-handed coordinate system, Orbiter uses left-handed one. Also, Blender and Orbiter use different UV coord origins
#  So, the module converts vertex and UV coordinates 
#  Conversion from orbiter coordinate system is: 
#  1. Coordinate system conversion:z=y ; y=-z; x=-x
#  2. Triangle backface flipping: tri[1]<->tri[2]
#  3. UV coord system conversion: v=1-v
#  So, conversion to orbiter is: z=-y,y=z,x=-x ; tri[1]<-> tri[2] ; v=1-v

ORBITER_PATH_DEFAULT="/home/vlad/programs/orbiter" #Change this to your Orbiter path

bl_addon_info = {
    "name": "Import Orbiter mesh (.msh)",
    "author": "vlad32768",
    "version": (1,0),
    "blender": (2, 5, 4),
    "api": 32391,
    "category": "Import/Export",
    "location": "File > Import > Orbiter mesh (.msh)",
    "warning": 'Beta version', # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/My_Script",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=#&group_id=#&atid=#",
    "description": """\
Imports Orbiter mesh file (as well as materials and textures) into Blender. Export feature coming soon.
"""}

import bpy

import io #file i/o
import os
import ntpath

####################################################
## IMPORT PART
####################################################
def create_mesh(name,verts,faces,norm,uv,show_single_sided):
    '''Function that creates mesh from loaded data'''

    me = bpy.data.meshes.new(name+"Mesh")
    ob = bpy.data.objects.new(name, me)
    ob.location =(0,0,0) #origin
    # Link object to scene
    bpy.context.scene.objects.link(ob)
    if show_single_sided:
        me.show_double_sided=False
    # from_pydata doesn't work correctly, it swaps vertices in some triangles 
    #me.from_pydata(verts,[], faces)
    me.vertices.add(len(verts))
    me.faces.add(len(faces))
    #me.vertices.foreach_set("co", verts)
    #me.faces.foreach_set("vertices_raw", unpackList(faces))
    for i in range(len(verts)):
        me.vertices[i].co=verts[i]
    for i in range(len(faces)):
        me.faces[i].vertices=faces[i]
    
    #there is something wrong with normals in Blender 
    #if (norm!=[]):
    #    for i in range(len(norm)):
    #        me.vertices[i].normal=norm[i]
    #        print (me.vertices[i].normal)

    if uv!=[]:
        #Loading UV tex coords
        uvtex=me.uv_textures.new()#create uvset
        for i in range(len(faces)):
            uvtex.data[i].uv1=uv[faces[i][0]]
            uvtex.data[i].uv2=uv[faces[i][1]]
            uvtex.data[i].uv3=uv[faces[i][2]]

    # Update mesh with new data
    me.update(calc_edges=True)
    return ob


def create_materials(groups,materials,textures,orbiterpath):
    #counting material/texture combinations
    print("Creating materials")
    matpairset=set()
    matpair=[]          # [(mat,tex),[mgroups...]]  Unique mat+tex and corresponding groups
    for n in range(len(groups)):
        l=(groups[n][1],groups[n][2])
        #print(l)
        if l not in matpairset:
            matpairset.add(l)
            matpair.append([l,[]]) #fill unique mat+tex combination
    for n in range(len(groups)):
        l=(groups[n][1],groups[n][2])
        for i in range(len(matpair)):
            if l==matpair[i][0]:
                matpair[i][1].append(n) #fill array of corresponding groups


    print("\nUnique pairs:\n",matpairset)
    print(matpair)
    
    #create textures
    #TODO: upper/lower case handling in Linux
    tx=[]
    tex_load_fails=0
    orbiter_path_ok=os.access(orbiterpath,os.F_OK)
    if not(orbiter_path_ok):
        print("Orbiter path is wrong! path=",orbiterpath)
    print("creating textures")
    for n in range(len(textures)):
        tx.append(bpy.data.textures.new(textures[n][1],"IMAGE"))
        if orbiter_path_ok:
            v=ntpath.split(textures[n][0])
            print(v);
            fpath=os.path.join(orbiterpath,"Textures")
            for i in v:
                fpath=os.path.join(fpath,i)
            print (fpath)
            #Trying to load data
            try:
                img=bpy.data.images.load(fpath)
            except:
                print("!!!!!Can not load image: ",fpath)
                tex_load_fails=tex_load_fails+1
                continue 
        else:
            tex_load_fails=tex_load_fails+1
            continue
        tx[n].image=img
        tx[n].use_alpha=True

    
    print("creating materials") 
    n=0
    matt=[]
    for pair in matpair:
        #create material object
        idx_mat=pair[0][0]-1
        idx_tex=pair[0][1]-1
        print("idx_mat=",idx_mat)
        print("mat_name=",materials[idx_mat][0])
        print("diff=",materials[idx_mat][1][:3])
        print("tex=",textures[idx_tex][1],"idx=",idx_tex)
        matt.append(bpy.data.materials.new(materials[idx_mat][0]))
        #diffuse component
        matt[n].diffuse_color=materials[idx_mat][1][:3]
        matt[n].alpha=materials[idx_mat][1][3]
        if materials[idx_mat][1][3]<1.0:
            matt[n].use_transparency=True
        #specular component
        matt[n].specular_color=materials[idx_mat][3][:3]
        matt[n].specular_alpha=materials[idx_mat][3][3]  
        if len(materials[idx_mat][3])==5:
            matt[n].specular_hardness=materials[idx_mat][3][4]
        
        #there aren''t different ambient and emissive color component in blender
        #ambient is very often equal to diffuse, it's like amb=1.0 in blender
        #Emmissive component:
        import_emmissive=True;
        if import_emmissive:
            emm_c=materials[idx_mat][4][:3]
            matt[n].emit=(emm_c[0]+emm_c[1]+emm_c[2])/3
        
        #Adding texture to material
        if idx_tex>=0:
            mtex=matt[n].texture_slots.add()
            mtex.texture=tx[idx_tex]
            mtex.texture_coords="UV" 
            #mtex.map_colordiff = True
            #mtex.map_alpha = True
            #mtex.map_coloremission = True
            #mtex.map_density = True
            #mtex.mapping = 'FLAT'

        for grp_idx in pair[1]:
            groups[grp_idx][5].data.materials.append(matt[n])
        n=n+1
    print("=============Materials creation summary:=================")
    print("Created ",n," materials,")
    print("Loaded ",len(tx)-tex_load_fails," textures.")
    if not(orbiter_path_ok):
        print("WARNING! Orbiter path is wrong or not accessible, textures cannot be loaded!")
        print("Wrong path=",orbiterpath)

    if tex_load_fails>0:
        print("WARNING! ",tex_load_fails," of ",len(tx)," textures aren't loaded, possibly wrong file name(s)!")

#load mesh function
def load_msh(filename,orbiterpath,convert_coords,show_single_sided):
    '''Read MSH file'''
    print("filepath=",filename,"orbiterpath=",orbiterpath)

    file=open(filename,"r")
    s=file.readline();
    if s!='MSHX1\n':
        print("This file is not orbiter mesh: ",s)
        return
    else:
        print("Orbiter mesh format detected ")
    n_groups=0  #N of groups from header
    n_materials=0   #N of mats from header
    n_textures=0    #N of texs from header
    n_grp=0         #real N of groups
    mat=[]          #mats in group (int)
    tex=[]          #texs in group (int)
    groups=[]       #groups description [label(str),mat(int),tex(int),nv(int),nt(int),obj(bpy.data.object)]
    materials=[]    #materials description [name,[diff RGBA],[amb RGBA],[spec RGBAP],[emit RGBA]]
    textures=[]     #[texture filename, texture name]
    while True:
        s=file.readline()
        if s=='': 
            break;
        v=s.split()
        #print (v)
        #------Reading GROUPS section-------------
        if v[0]=="GROUPS":
            print("------------------------Reading groups:----------------------------")
            n_groups=int(v[1]);
            
            n_mat=0; n_tex=0 #group material and texture
            label=""
            while n_grp<n_groups:
                s1=file.readline();
                v1=s1.split()

                #if v1[0]=="NONORMAL":
                #    print("NONORMAL!")
                if v1[0]=="LABEL":
                    label=v1[1]
                if v1[0]=="MATERIAL":
                    n_mat=int(v1[1].rstrip(";"))  #rstrip is for buggy files with ";" after digit
                if v1[0]=="TEXTURE":
                    n_tex=int(v1[1].rstrip(";"))  

                #Reading geometry
                if v1[0]=="GEOM":
                    vtx=[]
                    tri=[]
                    norm=[]
                    uv=[]
                    
                    nv=int(v1[1])
                    nt=int(v1[2].rstrip(";"))
                    #print ("Group No:",n_grp," verts=",nv," tris=",nt)
                    for n in range(nv):
                        s2=file.readline();
                        v2=s2.split();
                        #print(v2);
                        #if label=="cargodooroutL":
                        #    print("#####RAW DATA OF GEOM: ",label)
                        #    print (v2)
                        if convert_coords:
                            vtx.append([-float(v2[0]),-float(v2[2]),float(v2[1])])# convert from left-handed coord system
                        else: 
                            vtx.append([float(v2[0]),float(v2[1]),float(v2[2])]) #without conversion 
                        if len(v2)>5: #there are normals (not vtx+uvs only)
                            #should I convert the normals?
                            norm.append([float(v2[3]),float(v2[4]),float(v2[5])])
                        
                        convert_uvs=True; ##test mode= uvs without conversion
                        if len(v2)==8: #there are normals and uvs
                            if convert_uvs:
                                #in Blender, (0,0) is the upper-left corner. 
                                #in Orbiter -- lower-left corner. So I must invert V axis
                                uv.append([float(v2[6]),1.0-float(v2[7])])    
                            else:
                                uv.append([float(v2[6]),float(v2[7])])
                        elif len(v2)==5: #there are only uvs
                            if convert_uvs:
                                uv.append([float(v2[3]),1.0-float(v2[4])])    
                            else:
                                uv.append([float(v2[3]),float(v2[4])])

                    for n in range(nt): #read triangles
                        s2=file.readline();
                        v2=s2.split();
                        if convert_coords:
                            tri.append([int(v2[0]),int(v2[2]),int(v2[1])]) #reverted triangle
                        else:
                            tri.append([int(v2[0]),int(v2[1]),int(v2[2])]) #non reverted triangle
                    #print (vtx)
                    #print(norm)
                    n_grp=n_grp+1;
                    if label=='':
                        label="ORBGroup"+str(n_grp)
                    obj=create_mesh(label,vtx,tri,norm,uv,show_single_sided)
                    groups.append([label,n_mat,n_tex,nv,nt,obj])
                    label=""
        #--------------Reading MATERIALS section-----------------------        
        elif v[0]=="MATERIALS":
            n_materials=int(v[1])
            print("-------Reading Materials section,nmats=",n_materials,"------------")
            #material names
            for i in range (n_materials):
                materials.append([file.readline().strip()])
            #material properties
            for i in range (n_materials):
                file.readline(); # TODO: material name checking
                for n in range(4):
                    s1=file.readline()
                    v1=s1.split()
                    print("Reading material component,n=",n,"  comp=",v1)
                    if (n==2)and(len(v1)==5): #Specular,5 components
                        materials[i].append([float(v1[0]),float(v1[1]),float(v1[2]),float(v1[3]),float(v1[4])])
                    else:   #Other, 4 components
                        materials[i].append([float(v1[0]),float(v1[1]),float(v1[2]),float(v1[3])])
        #---------------Reading TEXTURES section------------------
        elif v[0]=="TEXTURES":
            print("-----------Reading TEXTURES section---------------")
            n_textures=int(v[1]);
            for i in range(n_textures):
                textures.append([file.readline().strip(),"ORBTexture"+str(i)])
       

   
    print("");
    print("==========================Summary===========================================")
    print("Headers: groups=",n_groups," materials=",n_materials," textures=",n_textures)
    print("\nData:\nGroups:")
    print(groups,"\nReal No=",len(groups))
    print("Materials:",materials) 
    print("Textures:",textures)
    file.close() #end reading file
    create_materials(groups,materials,textures,orbiterpath)
    return{"FINISHED"}

#for operator class properties
from bpy.props import *

class IMPORT_OT_msh(bpy.types.Operator):
    '''Import MSH Operator.'''
    bl_idname= "import_scene.msh"
    bl_label= "Import MSH"
    bl_description= "Import an Orbiter mesh (.msh)"
    bl_options= {'REGISTER', 'UNDO'}
    
    filepath= StringProperty(name="File Path", description="Filepath used for importing the MSH file", maxlen=1024, default="")
    
    #orbiterpath default for testing
    orbiterpath= StringProperty(name="Orbiter Path", description="Orbiter spacesim path", maxlen=1024, default=ORBITER_PATH_DEFAULT, subtype="DIR_PATH")
    
    convert_coords= BoolProperty(name="Convert coordinates", description="Convert coordinates between left-handed and right-handed systems ('yes' highly recomended)", default=True)
    show_single_sided= BoolProperty(name="Show single-sided", description="Disables 'Double Sided' checkbox, some models look better if enabled", default=True)

    def execute(self,context):
        print("execute")
        load_msh(self.filepath,self.orbiterpath,self.convert_coords,self.show_single_sided)
        return{"FINISHED"}

    def invoke(self,context,event):
        print("invoke")
        wm=context.window_manager
        wm.add_fileselect(self)
        return {"RUNNING_MODAL"}

def import_menu_function(self,context):
    self.layout.operator(IMPORT_OT_msh.bl_idname, text="Orbiter Mesh (.msh)")
############################################################
## END OF IMPORT PART
############################################################


# TODO: When importing, the script changes V to 1-V in UVTex, this should be done in export script
# 
# TODO: Conversion to Orbiter coord system must be done in export script (see description at addon info)

def register():
    print("registering...")
    bpy.types.INFO_MT_file_import.append(import_menu_function)
 
def unregister():
    print("unregistering...")
    bpy.types.INFO_MT_file_import.remove(import_menu_function)
 
if __name__ == "__main__":
    register()

