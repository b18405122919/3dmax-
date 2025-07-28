import os
import json
import pymxs
from pymxs import runtime as rt
import traceback

def safe_str(s):
    """安全转换值为字符串，处理特殊字符"""
    try:
        if s is None:
            return ""
        return str(s).replace('\\', '/').replace('"', "'")
    except:
        return ""

def debug_print(msg, level="INFO"):
    """打印调试信息到3ds Max监听器，支持不同级别"""
    try:
        timestamp = rt.execute('timestamp()')
        formatted_msg = f"[{level}] {safe_str(msg)}"
        rt.execute(f'print "{formatted_msg}"')
    except:
        # 如果pymxs不可用，使用普通print
        print(f"[{level}] {msg}")

def validate_file_path(file_path, file_type="文件"):
    """验证文件路径是否存在"""
    if not file_path:
        return False, f"{file_type}路径为空"
    if not os.path.exists(file_path):
        return False, f"{file_type}不存在: {file_path}"
    return True, ""

def load_textures(atlas_path, texture_dir):
    """从atlas文件加载纹理，改进的错误处理"""
    textures = {}
    
    # 验证输入路径
    valid, error_msg = validate_file_path(atlas_path, "Atlas文件")
    if not valid:
        debug_print(error_msg, "ERROR")
        return textures
    
    valid, error_msg = validate_file_path(texture_dir, "纹理目录")
    if not valid:
        debug_print(error_msg, "ERROR")
        return textures
    
    try:
        with open(atlas_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_texture = None
        loaded_count = 0
        error_count = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line: 
                continue
            
            try:
                if line.endswith('.png'):
                    tex_name = line.split('.')[0]
                    tex_path = os.path.join(texture_dir, line)
                    
                    if os.path.exists(tex_path):
                        # 检查纹理是否已经加载
                        if tex_name not in textures:
                            textures[tex_name] = rt.BitmapTexture(filename=tex_path)
                            current_texture = tex_name
                            loaded_count += 1
                            debug_print(f"加载纹理: {tex_name}")
                        else:
                            debug_print(f"纹理已存在，跳过: {tex_name}")
                    else:
                        debug_print(f"纹理文件未找到: {tex_path}", "WARNING")
                        error_count += 1
                        
                elif line.startswith('rotate:') and current_texture:
                    try:
                        rotation_value = float(line.split(':')[1])
                        textures[current_texture].rotation = rotation_value
                        debug_print(f"设置纹理旋转: {current_texture} = {rotation_value}")
                    except ValueError as e:
                        debug_print(f"旋转值解析错误: {line}", "WARNING")
                        
            except Exception as e:
                debug_print(f"处理第{line_num}行时出错: {str(e)}", "ERROR")
                error_count += 1
                
        debug_print(f"纹理加载完成: 成功{loaded_count}个, 失败{error_count}个")
        return textures
        
    except Exception as e:
        debug_print(f"纹理加载失败: {str(e)}", "ERROR")
        debug_print(f"详细错误: {traceback.format_exc()}", "ERROR")
        return {}

def create_bones(data, scale):
    """创建骨骼，改进的层次结构和定位"""
    bone_map = {}
    created_count = 0
    error_count = 0
    
    try:
        bones_data = data.get("bones", [])
        if not bones_data:
            debug_print("警告：未找到骨骼数据", "WARNING")
            return bone_map
        
        debug_print(f"开始创建{len(bones_data)}个骨骼")
        
        # 第一遍：创建所有骨骼
        for bone in bones_data:
            try:
                bone_name = safe_str(bone.get("name", ""))
                if not bone_name:
                    debug_print("跳过无名骨骼", "WARNING")
                    continue
                
                pos_x = float(bone.get("x", 0)) * scale
                pos_y = -float(bone.get("y", 0)) * scale  # 注意Y轴翻转
                pos_z = 0
                
                bone_length = max(0.1, float(bone.get("length", 1.0))) * scale
                end_pos = rt.Point3(pos_x, pos_y - bone_length, pos_z)
                
                # 创建骨骼
                new_bone = rt.BoneSys.createBone(
                    rt.Point3(pos_x, pos_y, pos_z),
                    end_pos,
                    rt.Point3(0, 0, 1)
                )
                
                new_bone.name = bone_name
                new_bone.width = bone_length * 0.3
                new_bone.height = bone_length * 0.3
                
                # 设置初始旋转
                if "rotation" in bone:
                    try:
                        rotation = rt.radToDeg(float(bone["rotation"]))
                        new_bone.rotation = rt.EulerAngles(0, 0, rotation)
                        debug_print(f"设置骨骼初始旋转: {bone_name} = {rotation}度")
                    except ValueError as e:
                        debug_print(f"旋转值解析错误: {bone_name}", "WARNING")
                
                bone_map[bone_name] = new_bone
                created_count += 1
                debug_print(f"创建骨骼: {bone_name} 位置({pos_x:.2f}, {pos_y:.2f})")
                
            except Exception as e:
                debug_print(f"骨骼创建失败 {bone.get('name', 'unknown')}: {str(e)}", "ERROR")
                error_count += 1
        
        # 第二遍：设置父子关系
        parent_relations = 0
        for bone in bones_data:
            try:
                bone_name = safe_str(bone.get("name", ""))
                parent_name = safe_str(bone.get("parent", ""))
                
                if parent_name and parent_name in bone_map and bone_name in bone_map:
                    bone_map[bone_name].parent = bone_map[parent_name]
                    parent_relations += 1
                    debug_print(f"设置父子关系: {bone_name} -> {parent_name}")
                elif parent_name and parent_name not in bone_map:
                    debug_print(f"父骨骼不存在: {parent_name}", "WARNING")
                    
            except Exception as e:
                debug_print(f"父子关系设置失败: {str(e)}", "ERROR")
        
        debug_print(f"骨骼创建完成: 成功{created_count}个, 错误{error_count}个, 父子关系{parent_relations}个")
        return bone_map
        
    except Exception as e:
        debug_print(f"骨骼创建失败: {str(e)}", "ERROR")
        debug_print(f"详细错误: {traceback.format_exc()}", "ERROR")
        return {}

def create_meshes(data, bone_map, textures):
    """创建网格对象，改进的材质处理"""
    mesh_count = 0
    error_count = 0
    
    slots_data = data.get("slots", [])
    if not slots_data:
        debug_print("警告：未找到槽位数据", "WARNING")
        return
    
    debug_print(f"开始创建{len(slots_data)}个网格")
    
    for slot in slots_data:
        try:
            slot_name = safe_str(slot.get("name", ""))
            bone_name = safe_str(slot.get("bone", ""))
            attachment = slot.get("attachment", {})
            
            if not slot_name:
                debug_print("跳过无名槽位", "WARNING")
                continue
                
            if bone_name not in bone_map:
                debug_print(f"为槽位{slot_name}找不到骨骼: {bone_name}", "WARNING")
                error_count += 1
                continue
                
            # 创建平面网格
            plane = rt.Plane(length=1, width=1)
            plane.name = f"Mesh_{slot_name}"
            plane.parent = bone_map[bone_name]
            plane.pos = bone_map[bone_name].pos
            
            # 应用纹理和材质
            if attachment and "name" in attachment:
                tex_name = attachment["name"].split('.')[0]
                if tex_name in textures:
                    # 创建材质
                    mat = rt.StandardMaterial()
                    mat.name = f"Mat_{tex_name}"
                    mat.diffuseMap = textures[tex_name]
                    plane.material = mat
                    
                    # 设置网格尺寸
                    if "width" in attachment and "height" in attachment:
                        try:
                            width = float(attachment["width"]) * 0.01
                            height = float(attachment["height"]) * 0.01
                            plane.width = width
                            plane.length = height
                            debug_print(f"设置网格尺寸: {slot_name} = {width:.3f}x{height:.3f}")
                        except ValueError as e:
                            debug_print(f"尺寸值解析错误: {slot_name}", "WARNING")
                    
                    debug_print(f"为{slot_name}应用纹理{tex_name}")
                else:
                    debug_print(f"为{slot_name}找不到纹理: {tex_name}", "WARNING")
            else:
                debug_print(f"槽位{slot_name}没有附件数据", "WARNING")
            
            mesh_count += 1
            
        except Exception as e:
            debug_print(f"网格创建失败 {slot.get('name', 'unknown')}: {str(e)}", "ERROR")
            error_count += 1
    
    debug_print(f"网格创建完成: 成功{mesh_count}个, 失败{error_count}个")

def import_animation(data, bone_map):
    """导入动画，使用更安全的关键帧创建方法"""
    try:
        debug_print("开始分析动画数据结构...")
        
        # 查找动画数据
        animations = data.get("animations", {})
        if not animations:
            debug_print("尝试查找其他动画键...")
            for key in data.keys():
                if "anim" in key.lower() or "motion" in key.lower():
                    debug_print(f"找到可能的动画键: {key}")
                    animations = data.get(key, {})
                    if animations:
                        break
        
        if not animations:
            debug_print("未找到动画数据", "WARNING")
            return
        
        debug_print(f"找到{len(animations)}个动画")
        debug_print(f"动画名称: {list(animations.keys())}")
        
        # 计算动画长度
        anim_length = 0
        for anim_name, anim_data in animations.items():
            bones_data = anim_data.get("bones", {})
            for bone_name, bone_anim in bones_data.items():
                for anim_type in ["translate", "rotate", "scale"]:
                    if anim_type in bone_anim:
                        frames = bone_anim[anim_type]
                        for frame in frames:
                            anim_length = max(anim_length, float(frame.get("time", 0)))
        
        # 转换为帧数（30帧/秒）
        anim_length = int(anim_length * 30) + 10
        rt.animationRange = rt.Interval(0, anim_length)
        rt.sliderTime = 0
        
        debug_print(f"动画长度: {anim_length}帧")
        
        # 导入每个动画
        imported_animations = 0
        for anim_name, anim_data in animations.items():
            debug_print(f"导入动画: {anim_name}")
            
            bones_data = anim_data.get("bones", {})
            for bone_name, bone_anim in bones_data.items():
                bone_name_str = safe_str(bone_name)
                if bone_name_str not in bone_map:
                    debug_print(f"动画找不到骨骼: {bone_name_str}", "WARNING")
                    continue
                    
                bone = bone_map[bone_name_str]
                
                # 位置动画
                if "translate" in bone_anim:
                    debug_print(f"处理{bone_name_str}的位置动画")
                    for frame in bone_anim["translate"]:
                        try:
                            time = int(float(frame.get("time", 0)) * 30)
                            x = float(frame.get("x", 0)) * 0.01
                            y = -float(frame.get("y", 0)) * 0.01
                            
                            rt.sliderTime = time
                            bone.pos = rt.Point3(x, y, 0)
                                
                        except Exception as e:
                            debug_print(f"位置关键帧错误: {str(e)}", "ERROR")
                
                # 旋转动画
                if "rotate" in bone_anim:
                    debug_print(f"处理{bone_name_str}的旋转动画")
                    for frame in bone_anim["rotate"]:
                        try:
                            time = int(float(frame.get("time", 0)) * 30)
                            angle = rt.radToDeg(float(frame.get("angle", 0)))
                            
                            rt.sliderTime = time
                            bone.rotation = rt.EulerAngles(0, 0, angle)
                                
                        except Exception as e:
                            debug_print(f"旋转关键帧错误: {str(e)}", "ERROR")
            
            imported_animations += 1
            debug_print(f"完成动画: {anim_name}")
        
        # 重置时间线到开始
        rt.sliderTime = 0
        
        debug_print(f"动画导入完成: 成功{imported_animations}个动画")
        
    except Exception as e:
        debug_print(f"动画导入失败: {str(e)}", "ERROR")
        debug_print(f"详细错误: {traceback.format_exc()}", "ERROR")

def import_spine(json_path, atlas_path, texture_dir, scale=1.0):
    """主导入函数，全面的错误处理"""
    try:
        debug_print("=== 开始Spine导入 ===")
        
        # 验证输入文件
        valid, error_msg = validate_file_path(json_path, "JSON文件")
        if not valid:
            return error_msg
            
        valid, error_msg = validate_file_path(atlas_path, "Atlas文件")
        if not valid:
            return error_msg
            
        valid, error_msg = validate_file_path(texture_dir, "纹理目录")
        if not valid:
            return error_msg
        
        # 加载JSON数据
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            debug_print("JSON数据加载成功")
        except Exception as e:
            return f"JSON文件读取失败: {str(e)}"
        
        # 导入组件
        debug_print("开始加载纹理...")
        textures = load_textures(atlas_path, texture_dir)
        
        debug_print("开始创建骨骼...")
        bone_map = create_bones(data, scale)
        
        debug_print("开始创建网格...")
        create_meshes(data, bone_map, textures)
        
        # 动画导入前重置时间线
        rt.sliderTime = 0
        rt.animationRange = rt.Interval(0, 100)
        
        debug_print("开始导入动画...")
        import_animation(data, bone_map)
        
        # 选择并缩放到导入的对象
        if bone_map:
            rt.select(list(bone_map.values()))
            rt.zoomExtents()
        
        debug_print("=== Spine导入成功完成 ===")
        return f"导入成功！创建了{len(bone_map)}个骨骼，加载了{len(textures)}个纹理"
        
    except Exception as e:
        error_msg = f"导入失败: {str(e)}"
        debug_print(error_msg, "ERROR")
        debug_print(f"详细错误: {traceback.format_exc()}", "ERROR")
        return error_msg

# 改进的UI设计
ui_script = """
try(destroyDialog spineImporterRollout)catch()

rollout spineImporterRollout "Spine动画导入工具 v2.0" width:500 height:450
(
    groupBox grpFiles "文件设置" width:480 height:160 pos:[10,10]
    groupBox grpOptions "选项" width:480 height:80 pos:[10,180]
    groupBox grpActions "操作" width:480 height:120 pos:[10,270]
    groupBox grpStatus "状态" width:480 height:100 pos:[10,400]
    
    -- 文件设置
    button btnJson "选择JSON文件" width:120 height:25 pos:[20,35]
    button btnAtlas "选择Atlas文件" width:120 height:25 pos:[20,70]
    button btnTex "选择纹理目录" width:120 height:25 pos:[20,105]
    button btnClear "清除所有" width:80 height:25 pos:[20,135]
    
    edittext edtJson "" width:330 height:25 pos:[150,35] readonly:true
    edittext edtAtlas "" width:330 height:25 pos:[150,70] readonly:true
    edittext edtTex "" width:330 height:25 pos:[150,105] readonly:true
    
    -- 选项
    label lblScale "缩放比例:" pos:[20,205]
    spinner spnScale "" range:[0.01,100,1.0] width:80 pos:[100,205]
    checkbox chkAnim "导入动画" checked:true pos:[200,205]
    checkbox chkPreview "创建预览" checked:true pos:[320,205]
    
    -- 操作
    button btnImport "开始导入" width:120 height:35 pos:[20,290]
    button btnTestAnim "测试动画" width:100 height:25 pos:[160,290]
    button btnReset "重置场景" width:100 height:25 pos:[280,290]
    button btnClose "关闭" width:80 height:25 pos:[400,290]
    button btnHelp "帮助" width:80 height:25 pos:[400,320]
    
    -- 状态
    label lblStatus "准备导入" pos:[20,415]
    progressBar pbProgress "" width:400 height:20 pos:[20,435]
    
    global json_path = ""
    global atlas_path = ""
    global tex_path = ""
    
    fn updateStatus msg = (
        lblStatus.text = msg
        pbProgress.value = 0
    )
    
    fn clearPaths = (
        json_path = ""
        atlas_path = ""
        tex_path = ""
        edtJson.text = ""
        edtAtlas.text = ""
        edtTex.text = ""
        updateStatus "准备导入"
    )
    
    on btnJson pressed do (
        path = getOpenFileName caption:"选择Spine JSON文件" types:"JSON文件|*.json|所有文件|*.*|"
        if path != undefined then (
            json_path = path
            edtJson.text = path
            updateStatus "已选择JSON文件"
        )
    )
    
    on btnAtlas pressed do (
        path = getOpenFileName caption:"选择Atlas文件" types:"Atlas文件|*.atlas|所有文件|*.*|"
        if path != undefined then (
            atlas_path = path
            edtAtlas.text = path
            updateStatus "已选择Atlas文件"
        )
    )
    
    on btnTex pressed do (
        path = getSavePath caption:"选择纹理目录"
        if path != undefined then (
            tex_path = path
            edtTex.text = path
            updateStatus "已选择纹理目录"
        )
    )
    
    on btnClear pressed do (
        clearPaths()
    )
    
    on btnImport pressed do (
        if json_path == "" then (messageBox "请选择JSON文件"; return())
        if atlas_path == "" then (messageBox "请选择Atlas文件"; return())
        if tex_path == "" then (messageBox "请选择纹理目录"; return())
        
        updateStatus "正在导入..."
        pbProgress.value = 25
        
        try (
            pbProgress.value = 50
            
            -- 执行导入
            result = python.execute ("import_spine(r'"+json_path+"', r'"+atlas_path+"', r'"+tex_path+"', "+ (spnScale.value as string)+")")
            
            pbProgress.value = 100
            updateStatus "导入完成"
            
            messageBox result title:"导入结果"
        ) catch (
            pbProgress.value = 0
            updateStatus "导入失败"
            messageBox ("错误: " + getCurrentException()) title:"错误"
        )
    )
    
    on btnTestAnim pressed do (
        try (
            updateStatus "动画数据已导入，请手动播放"
            messageBox "动画数据已导入完成，请手动播放测试" title:"动画测试"
        ) catch (
            messageBox "无法检查动画数据" title:"错误"
        )
    )
    
    on btnReset pressed do (
        try (
            rt.execute("delete objects")
            updateStatus "场景已清除"
            messageBox "场景已清除" title:"重置"
        ) catch (
            messageBox "清除场景时出错" title:"错误"
        )
    )
    
    on btnHelp pressed do (
        helpText = "Spine动画导入工具使用说明:\n\n" + \
                  "1. 选择Spine导出的JSON文件\n" + \
                  "2. 选择对应的Atlas文件\n" + \
                  "3. 选择包含纹理图片的目录\n" + \
                  "4. 调整缩放比例（可选）\n" + \
                  "5. 点击开始导入\n\n" + \
                  "注意事项:\n" + \
                  "- 确保所有文件路径正确\n" + \
                  "- 纹理文件应该在指定目录中\n" + \
                  "- 导入后可以手动调整动画"
        messageBox helpText title:"使用帮助"
    )
    
    on btnClose pressed do (
        destroyDialog spineImporterRollout
    )
)
"""

def create_ui():
    """创建并显示UI"""
    try:
        rt.execute(ui_script)
        rt.createDialog(rt.spineImporterRollout)
        debug_print("UI创建成功")
    except Exception as e:
        error_msg = f"UI创建失败: {safe_str(e)}"
        debug_print(error_msg, "ERROR")

# 启动UI
if __name__ == "__main__":
    create_ui()