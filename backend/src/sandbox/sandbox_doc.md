# Sandbox的实现思路
sandbox 是一个用于安全执行命令和文件操作的沙箱环境，采用了模块化的设计思想，主要包含以下核心组件和实现机制：
## 架构设计
- Sandbox 抽象基类 ( sandbox.py ): 定义沙箱核心接口
- SandboxProvider 抽象基类 ( sandbox_provider.py ): 定义沙箱的创建、获取和释放接口
- 具体实现 ( local/ ): 提供本地沙箱实现

## 核心功能
沙箱提供五大核心功能：

- execute_command : 执行bash命令
- read_file : 读取文件内容
- list_dir : 列出目录结构
- write_file : 写入文本内容
- update_file : 写入二进制内容

## 路径映射机制
实现了强大的路径映射功能：

- 正向解析 : 将容器路径映射到本地实际路径
- 反向解析 : 将本地路径转换回容器路径显示给用户
- 命令路径替换 : 执行前自动替换命令中的容器路径
- 输出路径替换 : 执行后自动替换输出中的本地路径

## 生命周期管理
通过中间件实现沙箱的智能生命周期管理：

- 懒加载机制 : 默认延迟到第一次工具调用时创建沙箱
- 线程内复用 : 同一线程内共享沙箱实例，避免频繁创建销毁
- 应用级释放 : 在应用关闭时统一释放所有沙箱资源
## 用户工具层
提供了简洁易用的工具函数：

- bash_tool : 执行bash命令
- ls_tool : 列出目录内容
- read_file_tool : 读取文件
- write_file_tool : 写入文件
- str_replace_tool : 替换文件内容
## 虚拟路径支持
实现了虚拟路径到实际路径的映射：

- /mnt/user-data/workspace/* → thread_data['workspace_path']/*
- /mnt/user-data/uploads/* → thread_data['uploads_path']/*
- /mnt/user-data/outputs/* → thread_data['outputs_path']/*
  
## 错误处理
定义了专门的异常类体系：

- SandboxError : 基础沙箱异常
- SandboxNotFoundError : 沙箱未找到异常
- SandboxRuntimeError : 沙箱运行时异常