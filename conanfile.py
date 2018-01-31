#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, VisualStudioBuildEnvironment, AutoToolsBuildEnvironment
import os


class LibnameConan(ConanFile):
    name = "czmq"
    version = "4.1.0"
    url = "https://github.com/bincrafters/conan-czmq"
    description = "High-level C binding for ØMQ"
    license = "MPL-2.0"
    exports = ["LICENSE.md"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = "shared=False"

    def system_requirements(self):
        if self.settings.os == 'Linux' and tools.os_info.is_linux:
            if tools.os_info.with_apt:
                installer = tools.SystemPackageTool()
                packages = ['autoconf', 'automake', 'libtool-bin']
                for package in packages:
                    installer.install(package)

    def requirements(self):
        self.requires.add('zmq/[>=4.2.2]@bincrafters/stable')

    def source(self):
        source_url = "https://github.com/zeromq/czmq"
        tools.get("{0}/archive/v{1}.tar.gz".format(source_url, self.version))
        extracted_dir = self.name + "-" + self.version

        os.rename(extracted_dir, 'sources')

    def build_vs(self):
        vs_version = int(str(self.settings.compiler.version))
        toolset = None
        if vs_version == 9:
            folder = 'vs2008'
        elif vs_version == 10:
            folder = 'vs2010'
        elif vs_version == 11:
            folder = 'vs2012'
        elif vs_version == 12:
            folder = 'vs2013'
        elif vs_version == 14:
            folder = 'vs2015'
        elif vs_version > 14:
            folder = 'vs2015'
            toolset = 'v141'
        runtime_library = {'MT': 'MultiThreaded',
                           'MTd': 'MultiThreadedDebug',
                           'MD': 'MultiThreadedDLL',
                           'MDd': 'MultiThreadedDebugDLL'}.get(str(self.settings.compiler.runtime))

        libzmq_props = os.path.join('sources', 'builds', 'msvc', 'vs2015', 'libczmq', 'libczmq.props')
        tools.replace_in_file(libzmq_props, '<ClCompile>',
                              '<ClCompile><RuntimeLibrary>%s</RuntimeLibrary>' % runtime_library)
        tools.replace_in_file(libzmq_props, '<Import Project="$(SolutionDir)libzmq.import.props" />', '')

        # generate platform.h
        with open(os.path.join('sources', 'builds', 'msvc', 'platform.h'), 'w') as f:
            f.write('#ifndef __PLATFORM_H_INCLUDED__\n')
            f.write('#define __PLATFORM_H_INCLUDED__\n')
            f.write('#define CZMQ_HAVE_WINDOWS 1\n')
            f.write('#define HAVE_LIBZMQ 1\n')
            f.write('#undef HAVE_UUID\n')
            f.write('#undef HAVE_SYSTEMD\n')
            f.write('#undef HAVE_LZ4\n')
            f.write('#define CZMQ_BUILD_DRAFT_API 1\n')
            f.write('#endif\n')

        if self.settings.build_type == 'Debug':
            config = 'DynDebug' if self.options.shared else 'StaticDebug'
        elif self.settings.build_type == 'Release':
            config = 'DynRelease' if self.options.shared else 'StaticRelease'
        with tools.chdir(os.path.join('sources', 'builds', 'msvc', folder)):
            command = tools.msvc_build_command(self.settings, 'czmq.sln', upgrade_project=False,
                                               build_type=config, targets=['libczmq'], toolset=toolset)
            if self.settings.arch == 'x86':
                command = command.replace('/p:Platform="x86"', '/p:Platform="Win32"')
            self.run(command)

    def build_configure(self):
        with tools.chdir("sources"):
            self.run('./autogen.sh')
            env_build = AutoToolsBuildEnvironment(self)
            if str(self.settings.compiler) in ['clang', 'gcc', 'apple-clang']:
                # workaround for linking C++ library (zmq) into c code (czmq)
                if str(self.settings.compiler.libcxx) in ['libstdc++', 'libstdc++11']:
                    env_build.libs.append('stdc++')
                elif str(self.settings.compiler.libcxx) == 'libc++':
                    env_build.libs.append('c++')
                # workaround for unused variables
                env_build.flags.append('-Wno-unused-variable')
                env_build.flags.append('-Wno-unused-function')
                env_build.flags.append('-Wno-unused-but-set-variable')
            prefix = os.path.abspath(self.package_folder)
            args = ['--prefix=%s' % prefix]
            if self.options.shared:
                args.extend(['--disable-static', '--enable-shared'])
            else:
                args.extend(['--disable-shared', '--enable-static'])
            env_build.configure(args=args)
            env_build.make()
            env_build.make(args=['install'])

    def build(self):
        if self.settings.compiler == 'Visual Studio':
            env_build = VisualStudioBuildEnvironment(self)
            with tools.environment_append(env_build.vars):
                self.build_vs()
        else:
            self.build_configure()

    def package(self):
        with tools.chdir("sources"):
            self.copy(pattern="LICENSE")
        if self.settings.compiler == 'Visual Studio':
            kind = 'dynamic' if self.options.shared else 'static'
            if self.settings.arch == 'x86':
                arch = 'Win32'
            elif self.settings.arch == 'x86_64':
                arch = 'x64'
            vs_version = {8: 'v80',
                          9: 'v90',
                          10: 'v100',
                          11: 'v110',
                          12: 'v120',
                          14: 'v140',
                          15: 'v141'}.get(int(str(self.settings.compiler.version)))
            libdir = os.path.join('sources', 'bin', arch, str(self.settings.build_type), vs_version, kind)
            self.copy(pattern='*.lib', src=libdir, dst='lib', keep_path=False)
            self.copy(pattern='*.dll', src=libdir, dst='bin', keep_path=False)
            self.copy(pattern='*.h', src=os.path.join('sources', 'include'), dst='include', keep_path=True)

    def package_info(self):
        if self.settings.compiler == 'Visual Studio':
            self.cpp_info.libs = ['libczmq', 'rpcrt4']
            if not self.options.shared:
                self.cpp_info.defines.append('CZMQ_STATIC')
        else:
            self.cpp_info.libs = ['czmq']
