#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spine动画导入工具使用示例
演示如何在3ds Max中使用该工具
"""

# 示例1: 基本导入
def basic_import_example():
    """基本导入示例"""
    print("📝 示例1: 基本导入")
    print("=" * 40)
    
    # 文件路径（需要根据实际情况修改）
    json_file = "C:/SpineProjects/character.json"
    atlas_file = "C:/SpineProjects/character.atlas"
    texture_dir = "C:/SpineProjects/textures"
    
    # 导入参数
    scale = 1.0  # 缩放比例
    
    print(f"📄 JSON文件: {json_file}")
    print(f"📋 Atlas文件: {atlas_file}")
    print(f"🖼️ 纹理目录: {texture_dir}")
    print(f"📏 缩放比例: {scale}")
    
    # 在3ds Max中执行导入
    # import_spine(json_file, atlas_file, texture_dir, scale)
    
    print("✅ 基本导入示例完成")

# 示例2: 批量导入
def batch_import_example():
    """批量导入示例"""
    print("\n📝 示例2: 批量导入")
    print("=" * 40)
    
    # 多个角色文件
    characters = [
        {
            "name": "角色1",
            "json": "C:/SpineProjects/char1.json",
            "atlas": "C:/SpineProjects/char1.atlas",
            "textures": "C:/SpineProjects/char1_textures",
            "scale": 1.0
        },
        {
            "name": "角色2", 
            "json": "C:/SpineProjects/char2.json",
            "atlas": "C:/SpineProjects/char2.atlas",
            "textures": "C:/SpineProjects/char2_textures",
            "scale": 0.8
        }
    ]
    
    for char in characters:
        print(f"🎭 导入角色: {char['name']}")
        print(f"   📄 JSON: {char['json']}")
        print(f"   📋 Atlas: {char['atlas']}")
        print(f"   🖼️ 纹理: {char['textures']}")
        print(f"   📏 缩放: {char['scale']}")
        
        # 在3ds Max中执行导入
        # import_spine(char['json'], char['atlas'], char['textures'], char['scale'])
        
        print(f"   ✅ {char['name']} 导入完成")
    
    print("✅ 批量导入示例完成")

# 示例3: 错误处理
def error_handling_example():
    """错误处理示例"""
    print("\n📝 示例3: 错误处理")
    print("=" * 40)
    
    # 测试各种错误情况
    error_cases = [
        {
            "name": "文件不存在",
            "json": "nonexistent.json",
            "atlas": "nonexistent.atlas", 
            "textures": "nonexistent_dir"
        },
        {
            "name": "空文件",
            "json": "empty.json",
            "atlas": "empty.atlas",
            "textures": "empty_dir"
        }
    ]
    
    for case in error_cases:
        print(f"🧪 测试: {case['name']}")
        
        try:
            # 在3ds Max中执行导入
            # result = import_spine(case['json'], case['atlas'], case['textures'])
            # print(f"   结果: {result}")
            print(f"   ⚠️ 预期会出错")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
    
    print("✅ 错误处理示例完成")

# 示例4: 自定义导入流程
def custom_import_example():
    """自定义导入流程示例"""
    print("\n📝 示例4: 自定义导入流程")
    print("=" * 40)
    
    def custom_import(json_path, atlas_path, texture_dir, scale=1.0):
        """自定义导入函数"""
        print(f"🚀 开始自定义导入...")
        
        # 1. 验证文件
        import os
        if not os.path.exists(json_path):
            return f"❌ JSON文件不存在: {json_path}"
        
        # 2. 加载数据
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 3. 分析数据结构
        bones_count = len(data.get("bones", []))
        slots_count = len(data.get("slots", []))
        animations_count = len(data.get("animations", {}))
        
        print(f"📊 数据统计:")
        print(f"   🦴 骨骼数量: {bones_count}")
        print(f"   🎨 槽位数量: {slots_count}")
        print(f"   🎬 动画数量: {animations_count}")
        
        # 4. 在3ds Max中执行导入
        # result = import_spine(json_path, atlas_path, texture_dir, scale)
        
        return f"✅ 自定义导入完成 - {bones_count}个骨骼, {slots_count}个槽位, {animations_count}个动画"
    
    # 使用自定义导入
    result = custom_import(
        "C:/SpineProjects/character.json",
        "C:/SpineProjects/character.atlas", 
        "C:/SpineProjects/textures",
        1.0
    )
    print(f"📋 结果: {result}")
    
    print("✅ 自定义导入流程示例完成")

# 示例5: UI使用
def ui_usage_example():
    """UI使用示例"""
    print("\n📝 示例5: UI使用")
    print("=" * 40)
    
    print("🖥️ 在3ds Max中启动UI:")
    print("1. 打开3ds Max")
    print("2. 运行脚本: execfile('spine_importer.py')")
    print("3. 在弹出的界面中:")
    print("   - 选择JSON文件")
    print("   - 选择Atlas文件") 
    print("   - 选择纹理目录")
    print("   - 设置缩放比例")
    print("   - 点击'开始导入'")
    
    print("✅ UI使用示例完成")

# 示例6: 调试技巧
def debugging_example():
    """调试技巧示例"""
    print("\n📝 示例6: 调试技巧")
    print("=" * 40)
    
    print("🔍 调试技巧:")
    print("1. 启用详细日志:")
    print("   - 在UI中勾选'详细日志'选项")
    print("   - 查看3ds Max监听器窗口")
    
    print("2. 分步测试:")
    print("   - 先测试纹理加载")
    print("   - 再测试骨骼创建")
    print("   - 最后测试动画导入")
    
    print("3. 文件验证:")
    print("   - 检查文件路径是否正确")
    print("   - 验证文件编码是否为UTF-8")
    print("   - 确认文件格式是否符合要求")
    
    print("4. 常见问题:")
    print("   - 如果看不到对象，检查缩放比例")
    print("   - 如果动画不播放，检查时间线设置")
    print("   - 如果纹理错误，检查文件路径")
    
    print("✅ 调试技巧示例完成")

def main():
    """主函数"""
    print("🎬 Spine动画导入工具使用示例")
    print("=" * 50)
    
    # 运行所有示例
    basic_import_example()
    batch_import_example()
    error_handling_example()
    custom_import_example()
    ui_usage_example()
    debugging_example()
    
    print("\n" + "=" * 50)
    print("🎉 所有示例演示完成！")
    print("📚 更多信息请参考README.md文件")

if __name__ == "__main__":
    main()