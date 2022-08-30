from inc_noesis import *
import copy
import noewin
import os
from ctypes import *




def registerNoesisTypes():
    handle = noesis.register("Xenoblade model import", ".wismt")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    xenoSkelHandle = noesis.registerTool("&Skeleton Override", xenoToolMenu)
    xenoLodHandle = noesis.registerTool("&Try Highest Level of Detail", xenoLodToggle)
    xenoMorphHandle = noesis.registerTool("&Skip Morph Data", xenoMorphToggle)
    noesis.setToolSubMenuName(xenoSkelHandle,"Xenoblade Switch")
    noesis.setToolSubMenuName(xenoLodHandle,"Xenoblade Switch")
    noesis.setToolSubMenuName(xenoMorphHandle,"Xenoblade Switch")

    noesis.checkToolMenuItem(xenoLodHandle,True)
    return 1
    
chrOverrideString = ""
wismt_header = 1297306180
wimdo_header = 1297632580
xbc1_header = 828596856

xenoLodFlag = True
xenoMorphFlag = False
xenoWimdoBoneFlag = False


def noepyCheckType(data):
    if len(data) < 8:
        return 0
    bs = NoeBitStream(data)
    Magic = bs.readInt()
    if Magic == wismt_header or Magic == xbc1_header:
        return 1
    else:
        return 0

    return 1

def noepyLoadModel(data, mdlList):
    FilePath = rapi.getDirForFilePath(rapi.getInputName())
    BaseFileName = rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getInputName()))

    wismt = NoeBitStream(data)
    Magic = wismt.readInt()
    if Magic == xbc1_header:
        tmpTex = None
        if FilePath[-3:] == "\\m\\":
            if rapi.checkFileExists(FilePath[:-3]+"\\h\\"+rapi.getLocalFileName(rapi.getInputName())):
                tmpTex = decomp_xbc1(NoeBitStream(rapi.loadIntoByteArray(FilePath[:-3]+"\\h\\"+rapi.getLocalFileName(rapi.getInputName()))),0)
        parse_texture(decomp_xbc1(wismt,0),mdlList,htex = tmpTex)
        return 1
        
    if chrOverrideString != "":
        CHRName = chrOverrideString
    else:
        CHRName = BaseFileName
    

    NoExtPath = rapi.getExtensionlessName(rapi.getInputName())
    if not rapi.checkFileExists(NoExtPath+".wimdo"):
        return 0
    wimdo = NoeBitStream((rapi.loadIntoByteArray(NoExtPath+".wimdo")))
    if wimdo.readInt() != wimdo_header:
        return 0  
    BoneTable = None    
    if rapi.checkFileExists(FilePath+CHRName+".chr"):
        skel = NoeBitStream((rapi.loadIntoByteArray(FilePath+CHRName+".chr")))
        BoneTable = parse_chr(skel)
    elif rapi.checkFileExists(FilePath+CHRName+".arc"):
        skel = NoeBitStream((rapi.loadIntoByteArray(FilePath+CHRName+".arc")))
        BoneTable = parse_chr(skel)
        
        
    wismt.seek(0x18)
    DataCount = wismt.readInt()
    DataOffset = wismt.readInt()+0x10
    ToCCount = wismt.readInt()
    ToCOffset = wismt.readInt()+0x10
    wismt.seek(0x44)
    TextureIDCount = wismt.readInt()
    TextureIDOffset = wismt.readInt()+0x10
    TextureNameTableOffset = wismt.readInt()
    
    ExternalTextureIDList = []
    TextureNameList = []
    wismt.seek(TextureIDOffset)
    for x in range(TextureIDCount):
        texID = wismt.readShort()
        ExternalTextureIDList.append(texID)
    
    if TextureNameTableOffset > 0:
        TextureNameTableOffset += 0x10
        wismt.seek(TextureNameTableOffset)
        textureCount = wismt.readInt()
        if 255>textureCount>0:
            textureOffsetTable = wismt.readInt()+TextureNameTableOffset
            for x in range(textureCount):
                wismt.seek(textureOffsetTable+0x10*x+0xc)
                texNameOffset = wismt.readInt()+TextureNameTableOffset
                wismt.seek(texNameOffset)
                texName = wismt.readString()
                TextureNameList.append(texName)
    for x in range(DataCount):
        wismt.seek(DataOffset+0x14*x)
        dataOffset = wismt.readInt()
        dataSize = wismt.readInt()
        wismt.seek(2,1)
        dataType = wismt.readShort()
        if dataType == 2:
            break
    toc = []
    wismt.seek(ToCOffset)
    for x in range(ToCCount):
        CompSize = wismt.readInt()
        DecompSize = wismt.readInt()
        xbc1Offset = wismt.readInt()
        toc.append(xbc1Offset)
    wismtDecomp = decomp_xbc1(wismt,toc[0])
    VertData,FaceData,WeightDefTable,WeightOffsetTable = parse_vert_data(wismtDecomp)
    texTable = parse_lbim(wismtDecomp,dataOffset,mdlList,TextureNameList)
    if ToCCount>1:
        toc2 = decomp_xbc1(wismt,toc[1])
        texTable2 = parse_lbim(toc2,0,mdlList,TextureNameList)
    else: texTable2 = None

    if ToCCount-2 == TextureIDCount and texTable2:
        for x in range(TextureIDCount):
            tmpImg = decomp_xbc1(wismt,toc[x+2])
            tmpIndex = ExternalTextureIDList[x]
            tmpH = texTable2[x].height*2
            tmpW = texTable2[x].width*2
            tmpF = texTable2[x].format
            tmpTex = parse_texture(tmpImg,mdlList,texName=TextureNameList[tmpIndex],H=tmpH,W=tmpW,F=tmpF)
            texTable[tmpIndex] = tmpTex
    mPath = FilePath[:-3]+"tex\\nx\\m\\"
    if os.path.exists(mPath):
        for x in range(TextureIDCount):
            tmpIndex = ExternalTextureIDList[x]
            tmpPath = mPath+TextureNameList[tmpIndex]+".wismt"
            if rapi.checkFileExists(tmpPath):
                tmpTex = decomp_xbc1(NoeBitStream(rapi.loadIntoByteArray(tmpPath)),0)
                if os.path.exists(mPath[:-2]+"h\\"):
                    tmpHTex = decomp_xbc1(NoeBitStream(rapi.loadIntoByteArray(mPath[:-2]+"h\\"+TextureNameList[tmpIndex]+".wismt")),0)
                    tmpTexOut = parse_texture(tmpTex,mdlList,htex = tmpHTex,texName=TextureNameList[tmpIndex])
                else:
                    tmpTexOut = parse_texture(tmpTex,mdlList,texName=TextureNameList[tmpIndex])
                texTable[tmpIndex] = tmpTexOut
    DataTable,MatTable,BoneTableFallback,LodDef = parse_wimdo(wimdo,TextureNameList,texTable)
    if BoneTable:
        tmpList = [i.name for i in BoneTable]
        tmpList2 = [i.name for i in BoneTableFallback]
        tmpList3 = [x for x in tmpList2 if x not in set(tmpList)]
        BoneTable = list(rapi.multiplyBones(BoneTable))
        tmpInt = len(BoneTable)
        if not xenoWimdoBoneFlag:
            for x in BoneTableFallback:
                if x.name in tmpList3:
                    x.parentIndex = 0
                    x.index = tmpInt
                    BoneTable.append(x)
                    tmpInt += 1
    elif not BoneTable and BoneTableFallback:
        BoneTable = BoneTableFallback
    ctx = rapi.rpgCreateContext()
    for d in DataTable:
        rapi.rpgClearBufferBinds()
        CurVert = VertData[d]
        if CurVert.get("BaseMorph",None):
            rapi.rpgBindPositionBufferOfs(CurVert["BaseMorph"], noesis.RPGEODATA_FLOAT, CurVert["BaseMorphSize"], 0)
            rapi.rpgBindNormalBufferOfs(CurVert["BaseMorph"], noesis.RPGEODATA_UBYTE, CurVert["BaseMorphSize"], 0xc)
            if not xenoMorphFlag:
                for m in CurVert["MorphTable"]:
                    rapi.rpgFeedMorphTargetPositionsOfs(m, noesis.RPGEODATA_FLOAT, CurVert["BaseMorphSize"], 0)
                    rapi.rpgFeedMorphTargetNormalsOfs(m, noesis.RPGEODATA_UBYTE, CurVert["BaseMorphSize"], 0xc)
                    rapi.rpgCommitMorphFrame(CurVert["VertCount"])
                rapi.rpgCommitMorphFrameSet()
        else:
            rapi.rpgBindPositionBufferOfs(CurVert["VertData"], noesis.RPGEODATA_FLOAT, CurVert["VertSize"], CurVert["VertDef"]["Vert"])
            if CurVert["VertDef"].get("Normal",None) != None:
                rapi.rpgBindNormalBufferOfs(CurVert["VertData"], noesis.RPGEODATA_BYTE, CurVert["VertSize"], CurVert["VertDef"]["Normal"])
                
        if CurVert["VertDef"].get("UV1",None) != None:
             rapi.rpgBindUV1BufferOfs(CurVert["VertData"], noesis.RPGEODATA_FLOAT, CurVert["VertSize"], CurVert["VertDef"]["UV1"])
        if CurVert["VertDef"].get("UV2",None) != None:
             rapi.rpgBindUV2BufferOfs(CurVert["VertData"], noesis.RPGEODATA_FLOAT, CurVert["VertSize"], CurVert["VertDef"]["UV2"])
        if CurVert["VertDef"].get("UV3",None) != None:
             rapi.rpgBindUVXBufferOfs(CurVert["VertData"], noesis.RPGEODATA_FLOAT, CurVert["VertSize"], 2,2,CurVert["VertDef"]["UV3"])
        if rapi.noesisIsExporting(): #Skip viewing vertex colors in preview
            if CurVert["VertDef"].get("VertColor",None) != None:
                 rapi.rpgBindColorBufferOfs(CurVert["VertData"], noesis.RPGEODATA_UBYTE, CurVert["VertSize"], CurVert["VertDef"]["VertColor"],4)
             
        if CurVert["VertDef"].get("WeightIndex",None) != None:
            weightRefTable = []
            for y in range(CurVert["VertCount"]):
                weightRefTable.append(noeUnpackFrom("i",CurVert["VertData"],CurVert["VertSize"]*y+CurVert["VertDef"]["WeightIndex"])[0])
            wOffset = 0
            if DataTable[d][0][7] == 2:
                wOffset = next((i[0] for i in WeightOffsetTable if i[1] == 1),0)
            BoneIndexBytes,WeightBytes = generate_weight_table(weightRefTable,WeightDefTable,BoneTable,BoneTableFallback,wOffset)
            rapi.rpgBindBoneIndexBuffer(BoneIndexBytes,noesis.RPGEODATA_USHORT,8,4)
            rapi.rpgBindBoneWeightBuffer(WeightBytes,noesis.RPGEODATA_USHORT,8,4)
        for x in DataTable[d]:
            if x[4] in LodDef or not xenoLodFlag:
                CurFace = FaceData[x[2]]
                rapi.rpgSetName(MatTable[x[3]].name+"_"+str(x[5]))
                rapi.rpgSetMaterial(MatTable[x[3]].name)
                rapi.rpgCommitTriangles(CurFace[0], noesis.RPGEODATA_USHORT,CurFace[1], noesis.RPGEO_TRIANGLE, 1)
    mdl = rapi.rpgConstructModelSlim()
    mdl.setModelMaterials(NoeModelMaterials(texTable,MatTable))
    if BoneTable:
        mdl.setBones(BoneTable)
    mdlList.append(mdl)    
    rapi.rpgClearBufferBinds()
    return 1

def parse_chr(CurFile):
    Magic = CurFile.readInt()
    if Magic != 1396789809:
        return None
    BoneTable = []
    CurFile.seek(0xC)
    SubFileCount = CurFile.readInt()
    SubFileOffset = CurFile.readInt()
    for x in range(SubFileCount):
        CurFile.seek(SubFileOffset+0x40*x)
        FileDataStart = CurFile.readInt()
        CurFile.seek(FileDataStart)
        FileMagic = CurFile.readInt()
        CurFile.seek(0x1c,1)
        FileType = CurFile.readInt()
        if FileMagic == 17218 and FileType ==6:
            CurFile.seek(FileDataStart+0x50)
            ParentTable = CurFile.readInt()+FileDataStart
            CurFile.seek(4,1)
            BoneCount = CurFile.readInt()
            CurFile.seek(4,1)
            NameTable = CurFile.readInt()+FileDataStart
            CurFile.seek(0xC,1)
            PositionTable = CurFile.readInt()+FileDataStart
            for y in range(BoneCount):
                CurFile.seek(ParentTable+2*y)
                BoneParent = CurFile.readShort()
                CurFile.seek(NameTable+0x10*y)
                NameOffset = CurFile.readInt()+FileDataStart
                CurFile.seek(NameOffset)
                BoneName = CurFile.readString()
                CurFile.seek(PositionTable+0x30*y)
                BonePos = NoeVec3.fromBytes(CurFile.readBytes(0xc))
                CurFile.seek(0x4,1)
                BoneRot = NoeQuat.fromBytes(CurFile.readBytes(0x10))
                BoneScale = NoeVec3.fromBytes(CurFile.readBytes(0xC))
                Mat1 = BoneRot.toMat43(1)
                Mat1[3] = BonePos
                BoneTable.append(NoeBone(y,BoneName,Mat1,parentIndex=BoneParent))
                
        else:
            continue
    return BoneTable

def decomp_xbc1(CurFile,xbOffset):
    CurFile.seek(xbOffset+8)
    DecompSize = CurFile.readInt()
    CompSize = CurFile.readInt()
    CurFile.seek(xbOffset+0x30)
    Output = NoeBitStream(rapi.decompInflate(CurFile.readBytes(CompSize),DecompSize))
    return Output
    
def parse_vert_data(CurFile):
    DefIndexTable = {
        0:"Vert",
        3:"WeightIndex",
        5:"UV1",
        6:"UV2",
        7:"UV3",
        17:"VertColor",
        28:"Normal",
        41:"WeightShort",
        42:"BoneID2",
    }
    VertData = []
    FaceData = []
    
    VertDefTable = CurFile.readInt()
    VertDefCount = CurFile.readInt()
    FaceDefTable = CurFile.readInt()
    FaceDefCount = CurFile.readInt()
    CurFile.seek(0x28)
    MorphOffset = CurFile.readInt()
    CurFile.seek(0x30)
    DataStart = CurFile.readInt()
    CurFile.seek(0x38)
    WeightOffset = CurFile.readInt()
    
    WeightDefIndex = None
    WeightDefTable = None
    WeightOffsetTable = []
    if WeightOffset > 0:
        CurFile.seek(WeightOffset)
        wOffsetCount = CurFile.readInt()
        wOffsetOffset = CurFile.readInt()
        WeightDefIndex = CurFile.readShort()
        for x in range(wOffsetCount):
            CurFile.seek(wOffsetOffset+(0x28*x)+4)
            wOffset = CurFile.readInt()
            CurFile.seek(0x14,1)
            testFlag = CurFile.readShort()
            WeightOffsetTable.append([wOffset,testFlag])

    for x in range(VertDefCount):    
        CurFile.seek(VertDefTable+x*0x20)
        ChunkStart = CurFile.readInt()+DataStart
        VertCount = CurFile.readInt()
        VertSize = CurFile.readInt()
        VertDef = CurFile.readInt()
        VertDefDataCount = CurFile.readInt()
        
        CurFile.seek(VertDef)
        VertDefOutput = {}
        DefOffset = 0
        
        tmpTab = []
        for y in range(VertDefDataCount):
            DefType = CurFile.readShort()
            tmpTab.append(DefType)
            DefLength = CurFile.readShort()
            DefTypeLookup = DefIndexTable.get(DefType)
            if DefTypeLookup:
                VertDefOutput[DefTypeLookup] = DefOffset
            DefOffset+=DefLength
        if x == WeightDefIndex:
            WeightDefTable = []
            for y in range(VertCount):
                CurFile.seek(ChunkStart+VertSize*y)
                Weights = noeUnpack("4H",CurFile.readBytes(8))
                BoneWeightIndexes = noeUnpack("4B",CurFile.readBytes(4))
                WeightDefTable.append([BoneWeightIndexes,Weights])
        CurFile.seek(ChunkStart)
        VertChunk = CurFile.readBytes(VertCount*VertSize)
        VertData.append({"VertData":VertChunk,"VertDef":VertDefOutput,"VertSize":VertSize,"VertCount":VertCount})
        
    for x in range(FaceDefCount):
        CurFile.seek(FaceDefTable+x*0x14)
        FaceDataStart = CurFile.readInt()+DataStart
        FaceDataCount = CurFile.readInt()
        CurFile.seek(FaceDataStart)
        FaceChunk = CurFile.readBytes(FaceDataCount*2)
        FaceData.append([FaceChunk,FaceDataCount])
    
    if MorphOffset > 0:
        CurFile.seek(MorphOffset)
        MorphDescriptorCount = CurFile.readInt()
        MorphDescriptorOffset = CurFile.readInt()
        TargetCount = CurFile.readInt()
        TargetOffset = CurFile.readInt()
        for x in range(MorphDescriptorCount):
            CurFile.seek(MorphDescriptorOffset+0x14*x)
            BufferIndex =CurFile.readInt()
            TargetIndexStart = CurFile.readInt()
            TargetIndexCount = CurFile.readInt()
            CurFile.seek(TargetOffset+0x10*TargetIndexStart)
            BaseDataStart = DataStart+CurFile.readInt()
            BaseVertCount = CurFile.readInt()
            BaseChunkSize = CurFile.readInt()
            CurFile.seek(BaseDataStart)
            BaseMorphBuffer = CurFile.readBytes(BaseVertCount*BaseChunkSize)
            VertData[BufferIndex]["BaseMorph"] = BaseMorphBuffer
            VertData[BufferIndex]["BaseMorphSize"] = BaseChunkSize
            VertData[BufferIndex]["MorphTable"] = []
            for y in range(TargetIndexCount):
                CurFile.seek(TargetOffset+0x10*TargetIndexStart+0x20+0x10*y)
                MorphDataStart = DataStart+CurFile.readInt()
                MorphVertCount = CurFile.readInt()
                MorphChunkSize = CurFile.readInt()
                tmpBuffer = copy.copy(BaseMorphBuffer)
                tmpStream = NoeBitStream(tmpBuffer)
                for z in range(MorphVertCount):
                    CurFile.seek(MorphDataStart+MorphChunkSize*z)
                    tmpX = CurFile.readFloat()
                    tmpY = CurFile.readFloat()
                    tmpZ = CurFile.readFloat()
                    CurFile.seek(4,1)
                    tmpNormals1 = CurFile.readUByte()
                    tmpNormals2 = CurFile.readUByte()
                    tmpNormals3 = CurFile.readUByte()
                    CurFile.seek(9,1)
                    tmpVertIndex = CurFile.readInt()
                    tmpStream.seek(0x20*tmpVertIndex)
                    tmpX = tmpX + tmpStream.readFloat()
                    tmpY = tmpY + tmpStream.readFloat()
                    tmpZ = tmpZ + tmpStream.readFloat()
                    tmpStream.seek(0x20*tmpVertIndex)
                    tmpStream.writeFloat(tmpX)
                    tmpStream.writeFloat(tmpY)
                    tmpStream.writeFloat(tmpZ)
                    tmpStream.writeUByte(tmpNormals1)
                    tmpStream.writeUByte(tmpNormals2)
                    tmpStream.writeUByte(tmpNormals3)
                tmpStream.seek(0)
                VertData[BufferIndex]["MorphTable"].append(tmpStream.getBuffer())
    return (VertData,FaceData,WeightDefTable,WeightOffsetTable)
    
def parse_wimdo(CurFile,TextureNameList,texTable):
    CurFile.seek(8)
    MeshOffset = CurFile.readInt()
    MaterialOffset = CurFile.readInt()
    
    MatTable = parse_materials(CurFile,MaterialOffset,TextureNameList,texTable)
    
    CurFile.seek(MeshOffset+0x1c)
    DataOffset = CurFile.readInt()+MeshOffset
    DataCount = CurFile.readInt()
    CurFile.read(4)
    BoneOffset = CurFile.readInt()
    CurFile.seek(MeshOffset+0x8c)
    LodDefOffset = CurFile.readInt()
    
    if LodDefOffset > 0:
        LodDef = []
        LodDefOffset += MeshOffset
        CurFile.seek(LodDefOffset+0xc)
        LodDefDataOffset = CurFile.readInt()+LodDefOffset
        LodDefDataCount = CurFile.readInt()
        CurFile.seek(LodDefDataOffset)
        for x in range(LodDefDataCount):
            LodIndex = CurFile.readShort()
            CurFile.seek(2,1)
            LodDef.append(LodIndex+1)
    else:
        LodDef = [1]
    BoneTable = None
    DataTable = {}
    DupeCheck = []
    BoneTable = []

    for x in range(DataCount):
        CurFile.seek(DataOffset+0x44*x)
        SubDataOffset = CurFile.readInt()+MeshOffset
        SubDataCount = CurFile.readInt()
        for y in range(SubDataCount):
            CurFile.seek(SubDataOffset+4+y*0x30)
            MeshFlag = CurFile.readInt()
            VertIndex = CurFile.readShort()
            FaceIndex = CurFile.readShort()
            CurFile.read(2)
            MatIndex = CurFile.readShort()
            CurFile.read(14)
            Lod = CurFile.readShort()
            if Lod == 0: Lod = 1 #temp fix?
            Group = CurFile.readShort()
            SubTab = [x,VertIndex,FaceIndex,MatIndex,Lod,y,Group,MeshFlag]
            DataEntry = DataTable.get(VertIndex)
            if not DataEntry:
                DataEntry = DataTable[VertIndex]=[]
            if str(VertIndex)+"_"+str(FaceIndex) not in DupeCheck:
                DupeCheck.append(str(VertIndex)+"_"+str(FaceIndex))
                DataEntry.append(SubTab)

    if BoneOffset > 0:
        BoneOffset+=MeshOffset
        CurFile.seek(BoneOffset+4)
        BoneCount = CurFile.readInt()
        BoneNameTableOffset = CurFile.readInt()
        BoneMatrixTableOffset = BoneOffset+CurFile.readInt()
        CurFile.seek(4,1)
        BonePositionTableOffset = BoneOffset+CurFile.readInt()
        BoneParent = -1

        for x in range(BoneCount):
            CurFile.seek(BoneMatrixTableOffset+0x40*x)
            tmpMatrix = NoeMat44.fromBytes(CurFile.read(0x40)).toMat43()
            tmpMatrix = tmpMatrix.inverse()
            CurFile.seek((BoneOffset+BoneNameTableOffset)+0x18*x)
            BoneNameOffset = BoneOffset+CurFile.readInt()
            CurFile.seek(4,1)
            BoneType = CurFile.readInt()
            BoneIndex = CurFile.readInt()
            CurFile.seek(BoneNameOffset)
            BoneName = CurFile.readString()
            if x > 0: BoneParent = 0
            BoneTable.append(NoeBone(x,BoneName,tmpMatrix,parentIndex = BoneParent))

        CurFile.seek(BoneOffset+0x28)
        BonePairOffset = CurFile.readInt()
        if BoneNameTableOffset == 0x3c and BonePairOffset > 0:
            CurFile.seek(BoneOffset+BonePairOffset)
            BoneParentOffset = CurFile.readInt()+BoneOffset
            BoneParentCount = CurFile.readInt()
            for x in range(BoneParentCount):
                CurFile.seek(BoneParentOffset+0x50*x)
                Child1 = CurFile.readShort()
                Parent1 = CurFile.readShort()
                Child2 = CurFile.readShort()
                Parent2 = CurFile.readShort()
                BoneTable[Child1].parentIndex = -1
                BoneTable[Child2].parentIndex = -1
                BoneTable[Child1].parentName = BoneTable[Parent1].name
                BoneTable[Child2].parentName = BoneTable[Parent2].name
    return DataTable,MatTable,BoneTable,LodDef
    
def parse_materials(CurFile,MaterialTableOffset,TextureNameList,texTable,Itter = 0x74):
    CurFile.seek(MaterialTableOffset)
    MatOffset = CurFile.readInt()+MaterialTableOffset
    MatCount = CurFile.readInt()
        
    MatTable = []
    
    for i in range(MatCount):
        CurFile.seek(MatOffset + Itter*i)
        NameOffset = CurFile.readInt()+MaterialTableOffset
        CurFile.seek(0x8,1)
        MatColor = noeUnpack("ffff",CurFile.readBytes(0x10))
        CurFile.seek(0x4,1)
        MatTexTableOffset = CurFile.readInt()+MaterialTableOffset
        MatTexCount = CurFile.readInt()
        MatMirrorFlagTest = CurFile.readInt()
        AlbedoIndex = None
        if (MatTexTableOffset and MatTexCount) > 0:
            CurFile.seek(MatTexTableOffset)
            AlbedoIndex = CurFile.readShort()
            if MatMirrorFlagTest & 2 == 2: texTable[AlbedoIndex].setFlags(noesis.NTEXFLAG_WRAP_MIRROR_REPEAT)
        CurFile.seek(NameOffset)
        MatName = CurFile.readString()
        tmpMat = NoeMaterial(MatName,"" if AlbedoIndex == None or len(TextureNameList) == 0 else TextureNameList[AlbedoIndex]+".png")
        tmpMat.setMetal(0,0)
        tmpMat.setDiffuseColor(MatColor)
        tmpMat.setFlags(noesis.NMATFLAG_TWOSIDED)
        MatTable.append(tmpMat)
    return MatTable
    
    
def xenoToolMenu(toolIndex):
    r = noesis.userPrompt(noesis.NOEUSERVAL_STRING, "Enter CHR", "Entered CHR will be searched for instead of default", "")
    global chrOverrideString
    chrOverrideString = r
    return 0

def xenoLodToggle(handle):
    global xenoLodFlag
    xenoLodFlag = not xenoLodFlag
    noesis.checkToolMenuItem(handle,xenoLodFlag)
    return 0
    
def xenoMorphToggle(handle):
    global xenoMorphFlag
    xenoMorphFlag = not xenoMorphFlag
    noesis.checkToolMenuItem(handle,xenoMorphFlag)
    return 0

def generate_weight_table(weightRefTable,WeightDefTable,BoneTable,BoneTableFallback,wOffset):
    BoneIndexBytes = b''
    WeightBytes = b''
    for x in range(len(weightRefTable)):
        wDef = WeightDefTable[weightRefTable[x]+wOffset]
        tmpBIndex = []
        for y in range(4):
            if (y > 0 and wDef[0][y] == 0):
                tmpBIndex.append(0)
            else:
                BoneIndex = next((i for i, item in enumerate(BoneTable) if item.name == (BoneTableFallback[wDef[0][y]].name )), 0)#might need to fix if 0 causes errors #or "AS_"+BoneTableFallback[wDef[0][y]].name[3:]
                tmpBIndex.append(BoneIndex)
        BoneIndexBytes += noePack("4H",*tmpBIndex)
        WeightBytes += noePack("4H",*wDef[1])
    return BoneIndexBytes,WeightBytes

def parse_texture(CurFile,mdlList,htex = None,Offset = 0,FileSize = None,texName = None,H=None,W=None,F=None):
    if not texName: texName = rapi.getInputName()
    if not FileSize:
        FileSize = CurFile.getSize()
    CurFile.seek(Offset+FileSize-4)
    lbim = CurFile.readInt()
    if lbim == 1296646732:
        CurFile.seek(Offset+FileSize-0x10)
        iFormat = CurFile.readInt()
        CurFile.seek(Offset+FileSize-0x20)
        xSize = CurFile.readInt()
        ySize = CurFile.readInt()
    elif (H and W) != None:
        iFormat = F
        xSize = W
        ySize = H
    else:
        return None
    if htex:
        data = htex.readBytes(htex.getSize())
        xSize = xSize*2
        ySize = ySize*2
    else:
        CurFile.seek(Offset)
        data = CurFile.readBytes(FileSize)
        
    if xSize<4:xSize = 4
    if ySize<4:ySize = 4
    
    if iFormat == 66:
        format = noesis.NOESISTEX_DXT1
    elif iFormat == 68:
        format = noesis.NOESISTEX_DXT5
    elif iFormat == 73:
        format = noesis.FOURCC_BC4
    elif iFormat == 75:
        format = noesis.FOURCC_BC5
    elif iFormat == 77:
        format = noesis.FOURCC_BC7
    else:
        format = noesis.NOESISTEX_DXT1
    
    blockWidth = 2 if iFormat == 37 else 4
    blockHeight = 1 if iFormat == 37 else 4
    blockSize = 8
    if format == noesis.FOURCC_BC5 or format == noesis.FOURCC_BC7 or format == noesis.NOESISTEX_DXT5: blockSize = 16
    mbH = 4 
    if xSize < 512 and xSize == ySize:
        mbH = 3
    if xSize < 256 and xSize == ySize:
        mbH = 2
    if xSize < 128 and xSize == ySize:
        mbH = 1
    if xSize != ySize:
        if xSize == 1024 and ySize < 1024:
            mbH = 4
        if xSize == 1024 and ySize < 512:
            mbH = 3
        if xSize == 512 and ySize < 512:
            mbH = 4
        if xSize == 512 and ySize <= 256:
            mbH = 3
        if xSize == 512 and ySize <= 129:
            mbH = 2
        if xSize == 512 and ySize <= 65:
            mbH = 1
        if xSize == 256 and ySize < 1025:
            mbH = 4
        if xSize == 256 and ySize < 512:
            mbH = 3
        if xSize == 256 and ySize < 256:
            mbH = 2
        if xSize == 256 and ySize < 128:
            mbH = 1
        if xSize == 128 and ySize < 513:
            mbH = 4
        if xSize == 128 and ySize < 257:
            mbH = 3
        if xSize == 128 and ySize < 128:
            mbH = 1
        if xSize == 64 and ySize < 257:
            mbH = 3
        if xSize == 64 and ySize < 129:
            mbH = 2
    
    if iFormat == 37:
        mbH = 4
    maxBlockHeight = rapi.callExtensionMethod("untile_blocklineargob_blockheight", ySize, mbH)
    widthInBlocks = (xSize + (blockWidth - 1)) // blockWidth
    heightInBlocks = (ySize + (blockHeight - 1)) // blockHeight
    data = rapi.callExtensionMethod("untile_blocklineargob", data, widthInBlocks, heightInBlocks, blockSize, maxBlockHeight)
    if iFormat == 37:
        data = rapi.imageDecodeRaw(data, xSize, ySize, "r8g8b8a8")
    else:
        data = rapi.imageDecodeDXT(data, xSize, ySize, format)
    tex = NoeTexture(texName, xSize, ySize, data)
    tex.format = iFormat
    return tex
        
def parse_lbim(CurFile,Offset,mdlList,texNameList):
    FileSize = CurFile.getSize()
    CurOffset = Offset
    lbimList = []
    lbimStart = Offset
    texTable = []
    while CurOffset < FileSize:
        CurFile.seek(CurOffset+0x1000-4)
        lbimCheck = CurFile.readInt()
        if lbimCheck == 1296646732:
            CurOffset += 0x1000
            lbimList.append([lbimStart,CurOffset-lbimStart])
            lbimStart = CurOffset
        else:
            CurOffset += 0x1000
            
    for x in lbimList:
        tex = parse_texture(CurFile,mdlList,Offset=x[0],FileSize=x[1],texName = texNameList[lbimList.index(x)])
        texTable.append(tex)
    return texTable
