import os
import json
import pymxs
from pymxs import runtime as rt

def safe_str(s):
    """安全转换值为字符串，处理特殊字符和编码问题"""
    try:
        if s is None:
            return ""
        return str(s).replace('\\', '/').replace('"', "'").replace('\n', ' ').strip()
    except:
        return ""

def debug_print(msg):
    """打印调试信息到3ds Max监听器，支持中文"""
    try:
        safe_msg = safe_str(msg)
        rt.execute(f'print "{safe_msg}"')
    except:
        # 如果pymxs执行失败，尝试其他方法
        try:
            rt.execute('print "' + safe_str(msg) + '"')
        except:
            pass

def load_textures(atlas_path, texture_dir):
    """从atlas文件加载纹理，改进的错误处理和中文提示"""
    textures = {}
    try:
        if not os.path.exists(atlas_path):
            debug_print(f"❌ Atlas文件未找到: {atlas_path}")
            return textures
            
        debug_print(f"📁 正在读取Atlas文件: {atlas_path}")
        
        with open(atlas_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_texture = None
        texture_count = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line: continue
            
            try:
                if line.endswith('.png'):
                    tex_name = line.split('.')[0]
                    tex_path = os.path.join(texture_dir, line)
                    if os.path.exists(tex_path):
                        textures[tex_name] = rt.BitmapTexture(filename=tex_path)
                        current_texture = tex_name
                        texture_count += 1
                        debug_print(f"✅ 加载纹理: {tex_name}")
                    else:
                        debug_print(f"⚠️ 纹理文件未找到: {tex_path}")
                elif line.startswith('rotate:') and current_texture:
                    try:
                        rotation_value = float(line.split(':')[1])
                        textures[current_texture].rotation = rotation_value
                        debug_print(f"🔄 设置纹理旋转: {current_texture} = {rotation_value}")
                    except:
                        debug_print(f"⚠️ 无法解析旋转值: {line}")
            except Exception as e:
                debug_print(f"❌ 处理第{line_num}行时出错: {str(e)}")
                
        debug_print(f"🎉 成功加载{texture_count}个纹理")
        return textures
    except Exception as e:
        debug_print(f"❌ 纹理加载失败: {str(e)}")
        return {}

def create_bones(data, scale):
    """创建骨骼，改进的层次结构和定位，支持中文骨骼名称"""
    bone_map = {}
    
    try:
        debug_print(f"🦴 开始创建骨骼，缩放比例: {scale}")
        
        # 第一遍：创建所有骨骼
        for bone in data.get("bones", []):
            try:
                bone_name = safe_str(bone["name"])
                pos_x = float(bone.get("x", 0)) * scale
                pos_y = -float(bone.get("y", 0)) * scale  # Y轴翻转
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
                
                # 如果指定了初始旋转
                if "rotation" in bone:
                    rotation = rt.radToDeg(float(bone["rotation"]))
                    new_bone.rotation = rt.EulerAngles(0, 0, rotation)
                    debug_print(f"🔄 设置初始旋转: {bone_name} = {rotation}°")
                
                bone_map[bone_name] = new_bone
                debug_print(f"✅ 创建骨骼: {bone_name} 位置({pos_x:.2f}, {pos_y:.2f})")
                
            except Exception as e:
                debug_print(f"❌ 骨骼创建失败 {bone.get('name', 'unknown')}: {str(e)}")
        
        # 第二遍：设置父子关系
        parent_count = 0
        for bone in data.get("bones", []):
            try:
                bone_name = safe_str(bone["name"])
                parent_name = safe_str(bone.get("parent"))
                
                if parent_name and parent_name in bone_map and bone_name in bone_map:
                    bone_map[bone_name].parent = bone_map[parent_name]
                    parent_count += 1
                    debug_print(f"👥 设置父子关系: {bone_name} -> {parent_name}")
            except Exception as e:
                debug_print(f"❌ 父子关系设置失败: {str(e)}")
        
        debug_print(f"🎉 成功创建{len(bone_map)}个骨骼，{parent_count}个父子关系")
        return bone_map
        
    except Exception as e:
        debug_print(f"❌ 骨骼创建失败: {str(e)}")
        return {}

def create_meshes(data, bone_map, textures):
    """创建网格对象，改进的材质处理和中文提示"""
    mesh_count = 0
    
    debug_print("🎨 开始创建网格对象...")
    
    for slot in data.get("slots", []):
        try:
            slot_name = safe_str(slot["name"])
            bone_name = safe_str(slot["bone"])
            attachment = slot.get("attachment", {})
            
            if bone_name not in bone_map:
                debug_print(f"⚠️ 为槽位{slot_name}找不到骨骼: {bone_name}")
                continue
                
            # 创建平面网格
            plane = rt.Plane(length=1, width=1)
            plane.name = f"Mesh_{slot_name}"
            plane.parent = bone_map[bone_name]
            plane.pos = bone_map[bone_name].pos
            
            # 如果可用则应用纹理
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
                        plane.width = float(attachment["width"]) * 0.01  # 缩小
                        plane.length = float(attachment["height"]) * 0.01
                        debug_print(f"📏 设置网格尺寸: {slot_name} = {plane.width:.2f} x {plane.length:.2f}")
                    
                    debug_print(f"✅ 为{slot_name}应用纹理{tex_name}")
                else:
                    debug_print(f"⚠️ 为{slot_name}找不到纹理: {tex_name}")
            else:
                debug_print(f"ℹ️ {slot_name}没有附件数据")
            
            mesh_count += 1
            
        except Exception as e:
            debug_print(f"❌ 网格创建失败 {slot.get('name', 'unknown')}: {str(e)}")
    
    debug_print(f"🎉 成功创建{mesh_count}个网格对象")

def import_animation(data, bone_map):
    """导入动画，使用更安全的关键帧创建方法和详细的中文提示"""
    try:
        debug_print("🎬 开始分析动画数据结构...")
        debug_print(f"📊 数据键: {list(data.keys())}")
        
        animations = data.get("animations", {})
        if not animations:
            debug_print("⚠️ 未找到动画数据")
            debug_print("🔍 尝试查找其他可能的动画键...")
            # 尝试其他可能的键名
            for key in data.keys():
                if "anim" in key.lower() or "motion" in key.lower():
                    debug_print(f"🔍 找到可能的动画键: {key}")
                    animations = data.get(key, {})
                    if animations:
                        break
        
        if not animations:
            debug_print("❌ 仍然未找到动画数据")
            debug_print("📋 打印数据结构预览:")
            debug_print(str(data)[:500])  # 只打印前500个字符
            return
        
        debug_print(f"🎬 找到动画数量: {len(animations)}")
        debug_print(f"📝 动画名称: {list(animations.keys())}")
        
        # 分析第一个动画的结构
        if animations:
            first_anim = list(animations.values())[0]
            debug_print(f"📋 第一个动画结构: {list(first_anim.keys())}")
            if "bones" in first_anim:
                debug_print(f"🦴 骨骼动画键: {list(first_anim['bones'].keys())}")
        
        # 计算动画长度
        anim_length = 0
        total_keyframes = 0
        
        for anim_name, anim_data in animations.items():
            debug_print(f"📊 分析动画: {anim_name}")
            bones_data = anim_data.get("bones", {})
            
            for bone_name, bone_anim in bones_data.items():
                for anim_type in ["translate", "rotate", "scale"]:
                    if anim_type in bone_anim:
                        frames = bone_anim[anim_type]
                        debug_print(f"🎯 找到 {anim_type} 动画，帧数: {len(frames)}")
                        total_keyframes += len(frames)
                        for frame in frames:
                            anim_length = max(anim_length, float(frame.get("time", 0)))
        
        # 转换为帧数（30帧/秒）
        anim_length = int(anim_length * 30) + 10
        rt.animationRange = rt.Interval(0, anim_length)
        rt.sliderTime = 0
        
        debug_print(f"⏱️ 动画长度: {anim_length}帧")
        debug_print(f"🎯 总关键帧数: {total_keyframes}")
        
        # 导入每个动画
        for anim_name, anim_data in animations.items():
            debug_print(f"🎬 导入动画: {anim_name}")
            
            # 处理骨骼动画
            bones_data = anim_data.get("bones", {})
            for bone_name, bone_anim in bones_data.items():
                bone_name_str = safe_str(bone_name)
                if bone_name_str not in bone_map:
                    debug_print(f"⚠️ 动画找不到骨骼: {bone_name_str}")
                    continue
                    
                bone = bone_map[bone_name_str]
                debug_print(f"🦴 处理骨骼动画: {bone_name_str}")
                
                # 位置动画
                if "translate" in bone_anim:
                    frame_count = len(bone_anim["translate"])
                    debug_print(f"📍 处理{bone_name_str}的位置动画，帧数: {frame_count}")
                    for i, frame in enumerate(bone_anim["translate"]):
                        try:
                            time = int(float(frame.get("time", 0)) * 30)
                            x = float(frame.get("x", 0)) * 0.01
                            y = -float(frame.get("y", 0)) * 0.01
                            
                            # 使用更安全的方法创建关键帧
                            rt.sliderTime = time
                            pos_controller = bone.pos.controller
                            if hasattr(pos_controller, 'addNewKey'):
                                rt.addNewKey(pos_controller, time)
                            bone.pos = rt.Point3(x, y, 0)
                                
                        except Exception as e:
                            debug_print(f"❌ 位置关键帧错误: {str(e)}")
                
                # 旋转动画
                if "rotate" in bone_anim:
                    frame_count = len(bone_anim["rotate"])
                    debug_print(f"🔄 处理{bone_name_str}的旋转动画，帧数: {frame_count}")
                    for i, frame in enumerate(bone_anim["rotate"]):
                        try:
                            time = int(float(frame.get("time", 0)) * 30)
                            angle = rt.radToDeg(float(frame.get("angle", 0)))
                            
                            # 使用更安全的方法创建关键帧
                            rt.sliderTime = time
                            rot_controller = bone.rotation.controller
                            if hasattr(rot_controller, 'addNewKey'):
                                rt.addNewKey(rot_controller, time)
                            bone.rotation = rt.EulerAngles(0, 0, angle)
                                
                        except Exception as e:
                            debug_print(f"❌ 旋转关键帧错误: {str(e)}")
                
                debug_print(f"✅ 完成{bone_name_str}的动画")
            
            debug_print(f"🎉 完成动画: {anim_name}")
        
        # 重置时间线到开始
        rt.sliderTime = 0
        
        debug_print("🎬 动画导入成功完成")
        
    except Exception as e:
        debug_print(f"❌ 动画导入失败: {str(e)}")
        import traceback
        debug_print(f"📋 详细错误: {traceback.format_exc()}")

def import_spine(json_path, atlas_path, texture_dir, scale=1.0):
    """主导入函数，全面的错误处理和中文提示"""
    try:
        debug_print("🚀 开始Spine动画导入...")
        
        # 验证输入文件
        if not os.path.exists(json_path):
            error_msg = f"❌ 错误：找不到JSON文件 {json_path}"
            debug_print(error_msg)
            return error_msg
            
        if not os.path.exists(atlas_path):
            error_msg = f"❌ 错误：找不到Atlas文件 {atlas_path}"
            debug_print(error_msg)
            return error_msg
            
        if not os.path.exists(texture_dir):
            error_msg = f"❌ 错误：找不到纹理目录 {texture_dir}"
            debug_print(error_msg)
            return error_msg
        
        debug_print("📄 正在加载JSON数据...")
        # 加载JSON数据
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        debug_print("✅ JSON数据加载成功")
        debug_print(f"📊 数据包含: {list(data.keys())}")
        
        # 导入组件
        debug_print("🖼️ 开始加载纹理...")
        textures = load_textures(atlas_path, texture_dir)
        
        debug_print("🦴 开始创建骨骼...")
        bone_map = create_bones(data, scale)
        
        debug_print("🎨 开始创建网格...")
        create_meshes(data, bone_map, textures)
        
        # 动画导入前重置时间线
        rt.sliderTime = 0
        rt.animationRange = rt.Interval(0, 100)
        
        debug_print("🎬 开始导入动画...")
        import_animation(data, bone_map)
        
        # 选择并缩放到导入的对象
        if bone_map:
            rt.select(list(bone_map.values()))
            rt.zoomExtents()
            debug_print("🔍 已缩放视图到导入的对象")
        
        success_msg = f"🎉 导入成功！创建了{len(bone_map)}个骨骼，{len(textures)}个纹理"
        debug_print(success_msg)
        return success_msg
        
    except Exception as e:
        error_msg = f"❌ 导入失败: {str(e)}"
        debug_print(error_msg)
        import traceback
        debug_print(f"📋 详细错误: {traceback.format_exc()}")
        return error_msg

# 改进的UI设计，支持中文界面
ui_script = """
try(destroyDialog spineImporterRollout)catch()

rollout spineImporterRollout "Spine动画导入工具 v2.0" width:520 height:450
(
    groupBox grpFiles "文件设置" width:500 height:170 pos:[10,10]
    groupBox grpOptions "导入选项" width:500 height:100 pos:[10,190]
    groupBox grpActions "操作控制" width:500 height:120 pos:[10,300]
    groupBox grpStatus "状态信息" width:500 height:100 pos:[10,430]
    
    -- 文件设置
    button btnJson "选择JSON文件" width:120 height:25 pos:[20,35]
    button btnAtlas "选择Atlas文件" width:120 height:25 pos:[20,70]
    button btnTex "选择纹理目录" width:120 height:25 pos:[20,105]
    button btnClear "清除所有" width:80 height:25 pos:[20,140]
    
    edittext edtJson "" width:350 height:25 pos:[150,35] readonly:true
    edittext edtAtlas "" width:350 height:25 pos:[150,70] readonly:true
    edittext edtTex "" width:350 height:25 pos:[150,105] readonly:true
    
    -- 导入选项
    label lblScale "缩放比例:" pos:[20,215]
    spinner spnScale "" range:[0.01,100,1.0] width:80 pos:[100,215]
    checkbox chkAnim "导入动画" checked:true pos:[200,215]
    checkbox chkPreview "创建预览" checked:true pos:[320,215]
    checkbox chkDebug "详细日志" checked:true pos:[420,215]
    
    -- 操作控制
    button btnImport "开始导入" width:120 height:35 pos:[20,320]
    button btnTestAnim "测试动画" width:100 height:25 pos:[160,320]
    button btnReset "重置场景" width:100 height:25 pos:[280,320]
    button btnHelp "帮助" width:80 height:25 pos:[400,320]
    button btnClose "关闭" width:80 height:25 pos:[420,350]
    
    -- 状态信息
    label lblStatus "准备导入" pos:[20,455]
    progressBar pbProgress "" width:400 height:20 pos:[20,475]
    label lblInfo "请选择文件并设置选项" pos:[20,500]
    
    global json_path = ""
    global atlas_path = ""
    global tex_path = ""
    
    fn updateStatus msg info:"" = (
        lblStatus.text = msg
        if info != "" then lblInfo.text = info
        pbProgress.value = 0
    )
    
    fn clearPaths = (
        json_path = ""
        atlas_path = ""
        tex_path = ""
        edtJson.text = ""
        edtAtlas.text = ""
        edtTex.text = ""
        updateStatus "准备导入" "请选择文件并设置选项"
    )
    
    on btnJson pressed do (
        path = getOpenFileName caption:"选择Spine JSON文件" types:"JSON文件|*.json|所有文件|*.*|"
        if path != undefined then (
            json_path = path
            edtJson.text = path
            updateStatus "已选择JSON文件" "请继续选择其他文件"
        )
    )
    
    on btnAtlas pressed do (
        path = getOpenFileName caption:"选择Atlas文件" types:"Atlas文件|*.atlas|所有文件|*.*|"
        if path != undefined then (
            atlas_path = path
            edtAtlas.text = path
            updateStatus "已选择Atlas文件" "请继续选择纹理目录"
        )
    )
    
    on btnTex pressed do (
        path = getSavePath caption:"选择纹理目录"
        if path != undefined then (
            tex_path = path
            edtTex.text = path
            updateStatus "已选择纹理目录" "所有文件已选择，可以开始导入"
        )
    )
    
    on btnClear pressed do (
        clearPaths()
    )
    
    on btnImport pressed do (
        if json_path == "" then (messageBox "请选择JSON文件"; return())
        if atlas_path == "" then (messageBox "请选择Atlas文件"; return())
        if tex_path == "" then (messageBox "请选择纹理目录"; return())
        
        updateStatus "正在导入..." "请稍候..."
        pbProgress.value = 25
        
        try (
            -- 获取导入选项
            import_anim = chkAnim.checked
            create_preview = chkPreview.checked
            debug_mode = chkDebug.checked
            
            pbProgress.value = 50
            
            -- 执行导入
            result = python.execute ("import_spine(r'"+json_path+"', r'"+atlas_path+"', r'"+tex_path+"', "+ (spnScale.value as string)+")")
            
            pbProgress.value = 100
            updateStatus "导入完成" "导入过程已完成"
            
            messageBox result title:"导入结果"
        ) catch (
            pbProgress.value = 0
            updateStatus "导入失败" "请检查错误信息"
            messageBox ("错误: " + getCurrentException()) title:"错误"
        )
    )
    
    on btnTestAnim pressed do (
        try (
            updateStatus "测试动画" "动画数据已导入，请手动播放测试"
            messageBox "动画数据已导入完成，请手动播放测试" title:"动画测试"
        ) catch (
            messageBox "无法检查动画数据" title:"错误"
        )
    )
    
    on btnReset pressed do (
        try (
            -- 清除场景
            rt.execute("delete objects")
            updateStatus "场景已清除" "所有对象已删除"
            messageBox "场景已清除" title:"重置"
        ) catch (
            messageBox "清除场景时出错" title:"错误"
        )
    )
    
    on btnHelp pressed do (
        help_text = "Spine动画导入工具使用说明:\n\n" + \
                   "1. 选择Spine导出的JSON文件\n" + \
                   "2. 选择对应的Atlas文件\n" + \
                   "3. 选择包含纹理图片的目录\n" + \
                   "4. 设置缩放比例和其他选项\n" + \
                   "5. 点击开始导入\n\n" + \
                   "支持的功能:\n" + \
                   "- 骨骼层次结构\n" + \
                   "- 纹理材质\n" + \
                   "- 位置和旋转动画\n" + \
                   "- 中文界面和提示"
        messageBox help_text title:"使用帮助"
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
        debug_print("✅ UI创建成功")
    except Exception as e:
        error_msg = f"❌ UI创建失败: {safe_str(e)}"
        debug_print(error_msg)
        rt.messageBox(error_msg)

# 启动UI
if __name__ == "__main__":
    debug_print("🚀 启动Spine动画导入工具...")
    create_ui()