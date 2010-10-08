#################################################################
## Important!
## TODO: When importing, the script changes V to 1-V in UVTex, this should be done in export script
## 
## TODO: Conversion to Orbiter coord system must be done in export script
##
## Conversion from orbiter is: 
##  1. Coordinate system conversion:z=y ; y=-z; x=-x
##  2. Triangle backface flipping: tri[1]<->tri[2]
##  3. UV coord system conversion: v=1-v
##
## Conversion to orbiter should be: z=-y,y=z,x=-x ; tri[1]<-> tri[2] ; v=1-v
##
##################################################################
bl_addon_info = {
    "name": "Import Orbiter mesh (.msh)",
    "author": "vlad32768",
    "version": (1,0),
    "blender": (2, 5, 4),
    "api": 31236,
    "category": "Import/Export",
    "location": "File > Import > Orbiter mesh (.msh)",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/My_Script",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=#&group_id=#&atid=#",
    "description": """\
This script imports Orbiter mesh file into Blender
"""}

import bpy

import io #file i/o


def create_mesh(name,verts,faces,norm,uv):
    '''Function that creates mesh from loaded data'''

    me = bpy.data.meshes.new(name+"Mesh")
    ob = bpy.data.objects.new(name, me)
    ob.location =(0,0,0) #origin
    #ob.draw_name = True
    # Link object to scene
    bpy.context.scene.objects.link(ob)
    # Create mesh from given verts, edges, faces. Either edges or
    # faces should be [], or you ask for problems
    me.from_pydata(verts,[], faces)
    # Update mesh with new data
    '''    
    if norm!=[]:
        for i in range(len(norm)):
            me.vertices[i].normal=norm[i]
            print (me.vertices[i].normal)
    '''
    if uv!=[]:
        #Loading UV tex coords
        uvtex=me.uv_textures.new()#create uvset
        print ("lenghts uvtexdata=",len(uvtex.data)," verts=",len(verts))
        for i in range(len(faces)):
            uvtex.data[i].uv1=uv[faces[i][0]]
            uvtex.data[i].uv2=uv[faces[i][1]]
            uvtex.data[i].uv3=uv[faces[i][2]]

    me.update(calc_edges=True)
    return ob


#load mesh function
def load_msh(filename,orbiterpath):
    '''Read MSH file'''
    print("filepath=",filename,"orbiterpath=",orbiterpath)

    file=open(filename,"r")
    s=file.readline();
    if s!='MSHX1\n':
        print("This file is not orbiter mesh: ",s)
        return
    else:
        print("Orbiter mesh format detected ")
    n_groups=n_grp=0
    groups=[]
    n_materials=n_mat=0
    mat=[]
    n_textures=n_tex=0
    tex=[]
    while True:
        s=file.readline()
        if s=='': 
            break;
        v=s.split()
        #print (v)
        #Reading GROUPS section
        if v[0]=="GROUPS":
            print("Reading groups:")
            n_groups=int(v[1]);
            while n_grp<n_groups:
                s1=file.readline();
                v1=s1.split()
                #Reading geometry
                if v1[0]=="GEOM":
                    vtx=[]
                    tri=[]
                    norm=[]
                    uv=[]
                    
                    nv=int(v1[1])
                    nt=int(v1[2])
                    print ("Group No:",n_grp," verts=",nv," tris=",nt)
                    for n in range(nv):
                        s2=file.readline();
                        v2=s2.split();
                        #print(v2);
                        # convert from left-handed coord system
                        #vtx.append([float(v2[0]),float(v2[1]),float(v2[2])]) #that was straightforward
                        vtx.append([-float(v2[0]),-float(v2[2]),float(v2[1])])
                        if len(v2)>3:
                            #should I convert the normals?
                            norm.append([float(v2[3]),float(v2[4]),float(v2[5])])
                        if len(v2)>6:
                            #in Blender, (0,0) is the upper-left corner. in Orbiter -- lower-left corner. So I must invert V axis
                            uv.append([float(v2[6]),1.0-float(v2[7])])
                    for n in range(nt): #read triangles
                        s2=file.readline();
                        v2=s2.split();
                        #tri.append([int(v2[0]),int(v2[1]),int(v2[2])]) #non reverted triangle
                        tri.append([int(v2[0]),int(v2[2]),int(v2[1])]) #reverted triangle
                    #print (vtx)
                    #print(norm)
                    create_mesh("Group"+str(n_grp),vtx,tri,norm,uv)

                    n_grp=n_grp+1;

        #Reading MATERIALS section        
        elif v[0]=="MATERIALS":
            n_materials=v[1]
        #Reading TEXTURES section
        elif v[0]=="TEXTURES":
            n_textures=v[1];
            

        #print(s,end='')
   
    print("");
    print("Summary: groups=",n_groups," materials=",n_materials," textures=",n_textures)
    #file 
    file.close()

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
    orbiterpath= StringProperty(name="Orbiter Path", description="Orbiter spacesim path", maxlen=1024, default="~/programs/orbiter", subtype="DIR_PATH")

    def execute(self,context):
        print("execute")
        load_msh(self.filepath,self.orbiterpath)
        return{"FINISHED"}

    def invoke(self,context,event):
        print("invoke")
        wm=context.window_manager
        wm.add_fileselect(self)
        return {"RUNNING_MODAL"}

def menu_function(self,context):
    self.layout.operator(IMPORT_OT_msh.bl_idname, text="Orbiter Mesh (.msh)")
    

def register():
    #bpy.types.register(MyOperator)
    print("registering...")
    bpy.types.INFO_MT_file_import.append(menu_function)
 
def unregister():
    print("unregistering...")
    #bpy.types.unregister(MyOperator)
    bpy.types.INFO_MT_file_import.remove(menu_function)
 
if __name__ == "__main__":
    register()

