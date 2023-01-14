import hashlib
import json
import os
import platform
import re
import subprocess
import threading
import urllib.request
import uuid

import FMCLCore.System.CoreMakeFolderTask
import FMCLCore.System.SystemAndArch
import FMCLCore.System.UnzipTask
import FMCLCore.System.Logging


def download_native(arg: dict):
    back_msg = threading.current_thread().name + " done with message: "
    e = 0
    emsg = ""
    for i in range(5):
        if os.path.exists(arg["path"]) and \
                (("size" not in arg) or (os.path.getsize(arg["path"]) == arg["size"])) and \
                (("sha1" not in arg) or (hashlib.sha1(open(arg["path"], "rb").read()).hexdigest() == arg["sha1"])):
            if "unzip" in arg:
                FMCLCore.System.Logging.showinfo("unzip" + str(arg))
                FMCLCore.System.UnzipTask.unzip(arg["path"], arg["unzip"])
            back_msg += f"Download successfully in {i} try(s) and {e} exception(s): {emsg}"
            break
        else:
            try:
                open(arg["path"], "wb+").write(urllib.request.urlopen(arg["url"], timeout=5).read())
            except Exception as exc:
                e += 1
                emsg += repr(exc)
    FMCLCore.System.Logging.showsuccess(back_msg)

def multprocessing_task(tasks: list, function, cores: int):
    threads = []

    def _run():
        while threads:
            if len(tasks) >= 1:
                task = tasks.pop()
                function(task)
            else: break

    for i in range(cores + 1):
        thread = threading.Thread(target=_run)
        thread.start()
        threads.append(thread)

    for thread in threads: thread.join()

def _checkRules(rules: dict):
    for i in rules:
        if i["action"] == "allow":
            if "os" in i:
                if "name" in i["os"] and FMCLCore.System.SystemAndArch.system() != i["os"]["name"]: return False
                elif "version" in i["os"] and not re.match(i["os"]["version"], platform.version()): return False
        elif i["action"] == "disallow":
            if "os" in i:
                if "name" in i["os"] and FMCLCore.System.SystemAndArch.system() == i["os"]["name"]: return False
                elif "version" in i["os"] and re.match(i["os"]["version"], platform.version()): return False
    return True

def launch(game_directory: str = ".minecraft", version_name: str = None, java: str = "java", playername: str = "player",
           UUID: str = uuid.uuid4().hex, TOKEN: str = "0", JvmMaxMemory: int = 1024, FixMaxThread: int = 64,
           UseJvmForPerformance: bool = False):
    cmdlist = []

    basic_jvm = [{'rules': [{'action': 'allow', 'os': {'name': 'osx'}}], 'value': ['-XstartOnFirstThread']},
                 {'rules': [{'action': 'allow', 'os': {'name': 'windows'}}], 'value': [
                     '-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump']},
                 {'rules': [{'action': 'allow', 'os': {'name': 'windows', 'version': '^10\\.'}}],
                  'value': ['-Dos.name=Windows 10', '-Dos.version=10.0']},
                 '-Djava.library.path=${natives_directory}', '-Dminecraft.launcher.brand=${launcher_name}',
                 '-Dminecraft.launcher.version=${launcher_version}', '-cp', '${classpath}']

    game_directory = os.path.realpath(game_directory)

    verpath = os.path.join(game_directory, "versions", version_name)
    libpath = os.path.join(verpath, "natives-" + FMCLCore.System.SystemAndArch.system())
    jsonpath = os.path.join(verpath, version_name + ".json")
    jarpath = os.path.join(verpath, version_name + ".jar")

    if version_name is None: return ["VERSION MUSTN'T BE NONE"]
    if not (os.path.exists(game_directory) and os.path.exists(jsonpath)):
        return 1

    ver_json = json.load(open(jsonpath))

    cmdlist.append(java)

    cmdlist.append("-Xmx" + str(JvmMaxMemory) + "m")
    if UseJvmForPerformance:
        cmdlist.append("-XX:+UnlockExperimentalVMOptions")
        cmdlist.append("-XX:+UseParallelGC")
        cmdlist.append("-XX:-OmitStackTraceInFastThrow")
        cmdlist.append("-XX:-DontCompileHugeMethods")
        cmdlist.append("-Dlog4j2.formatMsgNoLookups=true")
        cmdlist.append("-Djava.rmi.server.useCodebaseOnly=true")
        cmdlist.append("-Dcom.sun.jndi.cosnaming.object.trustURLCodebase=false")

    args = []
    if "arguments" in ver_json:
        for i in ver_json["arguments"]["jvm"]:
            if type(i) == str: cmdlist.append(i)
            elif _checkRules(i["rules"]):
                    if type(i["value"]) == str: cmdlist.append(i["value"])
                    else:
                        for j in i["value"]: cmdlist.append(j)
        for i in ver_json["arguments"]["game"]:
            if type(i) == str: args.append(i)
    else:
        args = ver_json["minecraftArguments"].split(" ")
        for i in basic_jvm:
            if type(i) == str: cmdlist.append(i)
            elif _checkRules(i["rules"]):
                    for j in i["value"]: cmdlist.append(j)

    cmdlist.append("${mainClass}")
    cmdlist += args

    cp = ""
    need_to_be_fixed = []

    if not os.path.exists(jarpath):
        need_to_be_fixed.append({
            "path": jarpath,
            "url": ver_json["downloads"]["client"]["url"],
            "size": ver_json["downloads"]["client"]["size"],
            "sha1": ver_json["downloads"]["client"]["sha1"]})

    for i in ver_json['libraries']: #遍历libraries数组
        if "name" in i:
            name = i["name"].split(":")  #<package>:<name>:<version>
            name[0] = name[0].replace(".", os.sep)
            p, n, v = name[0], name[1], name[2] #分配package, name, version
            rpath = os.path.join(game_directory, "libraries", p, n, v, n + "-" + v + ".jar") #获取jar path
            if ("rules" not in i) or _checkRules(i["rules"]): #如果未指定规则或者符合规则，就执行操作
                if ("downloads" not in i) or ("classifiers" not in i["downloads"]):
                    if "downloads" in i and "artifact" in i["downloads"]:
                        package = {
                            "path": os.path.join(game_directory, "libraries", i["downloads"]["artifact"]["path"]),
                            "url": i["downloads"]["artifact"]["url"],
                            "size": i["downloads"]["artifact"]["size"],
                            "sha1": i["downloads"]["artifact"]["sha1"]
                        }
                        FMCLCore.System.CoreMakeFolderTask.make_long_dir(os.path.dirname(package["path"]))
                        need_to_be_fixed.append(package)
                    elif "url" in i:
                        FMCLCore.System.CoreMakeFolderTask.make_long_dir(os.path.dirname(rpath))
                        need_to_be_fixed.append({
                            "path": rpath,
                            "url": i["url"] + p.replace("\\", "/") + "/" + n + "/" + v + "/" + n + "-" + v + ".jar"})
                    else:
                        FMCLCore.System.Logging.showerror("Failed to fix depend:" + rpath)


                    cp += os.path.realpath(rpath) + os.pathsep

                else: #若不是只有artifact键，则认为这是natives，下载并解压
                    rname = i["natives"][FMCLCore.System.SystemAndArch.system()]
                    package = {
                            "path": os.path.join(game_directory, "libraries", i["downloads"]["classifiers"][rname]["path"]),
                            "url": i["downloads"]["classifiers"][rname]["url"],
                            "unzip": libpath,
                            "size": i["downloads"]["classifiers"][rname]["size"],
                            "sha1": i["downloads"]["classifiers"][rname]["sha1"]
                        }
                    FMCLCore.System.CoreMakeFolderTask.make_long_dir(os.path.dirname(package["path"]))
                    FMCLCore.System.Logging.showinfo("Fix library:" + rpath)
                    need_to_be_fixed.append(package)

    multprocessing_task(need_to_be_fixed, download_native, FixMaxThread) #多线程下载依赖
    cp += jarpath #最终将Minecraft核心传入classpath

    arg = {
        "${mainClass}": ver_json["mainClass"],
        "${natives_directory}": libpath,
        "${launcher_name}": "FMCL",
        "${launcher_version}": "Rebuild",
        "${classpath}": cp,
        "${assets_root}": os.path.realpath(os.path.join(game_directory, "assets")),
        "${assets_index_name}": ver_json["assetIndex"]["id"],
        "${auth_uuid}": UUID,
        "${auth_access_token}": TOKEN,
        "${user_type}": "Mojang",
        "${version_type}": "FMCL",
        "${user_properties}": "{}",
        "${auth_session}": "{}",
        "${clientid}": "0",
        "${auth_xuid}": "0",
        "${game_assets}": "resources",
        "${auth_player_name}": playername,
        "${version_name}": version_name,
        "${game_directory}": game_directory
    } #这一串东西是字符串替换模板，用于设置正确的jvm/game参数

    for i in range(len(cmdlist)): #循环替换字符串模板
        for j in arg:
            cmdlist[i] = cmdlist[i].replace(j, arg[j])

    return cmdlist

# a = (launch(input(".minecraft路径："),
#              input("要启动的游戏版本："),
#              input("java路径(可只填写\"java\")："),
#              input("玩家名称："),
#             UUID='c8189b09aebf49838b65bad10e905ba6',
#             TOKEN='eyJhbGciOiJIUzI1NiJ9.eyJ4dWlkIjoiMjUzNTQwNzExMjg1Njg4OCIsImFnZyI6IkFkdWx0Iiwic3ViIjoiNDg1ZjI2ODUtOGJkZi00ZmNlLTkwZmUtMTcyMjZlNzYwZDc5IiwibmJmIjoxNjczNjA3MzU1LCJhdXRoIjoiWEJPWCIsInJvbGVzIjpbXSwiaXNzIjoiYXV0aGVudGljYXRpb24iLCJleHAiOjE2NzM2OTM3NTUsImlhdCI6MTY3MzYwNzM1NSwicGxhdGZvcm0iOiJVTktOT1dOIiwieXVpZCI6IjAxYTYxYWMyYTNiZTI5YjVmMjc2MTM2ZjIwNGZmMmM0In0.OdD4LGd9BE3aw9QjH0-iWhfuIT9PGg1EmJ5ZMP76oBs'))
# print(a)
# subprocess.run(a)
# input()