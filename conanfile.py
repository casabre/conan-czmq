#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, CMake
import os


class LibnameConan(ConanFile):
    name = "czmq"
    version = "4.1.0"
    url = "https://github.com/bincrafters/conan-czmq"
    description = "High-level C binding for ØMQ"
    license = "MPL-2.0"
    exports = ["LICENSE.md"]
    exports_sources = ['CMakeLists.txt']
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = "shared=False", "fPIC=True"
    generators = ['cmake']

    def configure(self):
        if self.settings.compiler == 'Visual Studio':
            del self.options.fPIC

    def requirements(self):
        self.requires.add('zmq/[>=4.2.2]@bincrafters/stable')

    def source(self):
        source_url = "https://github.com/zeromq/czmq"
        tools.get("{0}/archive/v{1}.tar.gz".format(source_url, self.version))
        extracted_dir = self.name + "-" + self.version

        os.rename(extracted_dir, 'sources')

    def build(self):
        if self.settings.compiler == 'Visual Studio':
            with tools.vcvars(self.settings, force=True, filter_known_paths=False):
                self.build_cmake()
        else:
            self.build_cmake()

    def build_cmake(self):
        cmake = CMake(self, generator='Ninja')
        if self.settings.compiler != 'Visual Studio':
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = self.options.fPIC
        cmake.configure(build_dir='build')
        cmake.build()
        cmake.install()

    def package(self):
        self.copy(pattern="LICENSE", src='sources', dst='license')

    def package_info(self):
        if self.settings.compiler == 'Visual Studio':
            self.cpp_info.libs = ['czmq' if self.options.shared else 'libczmq']
            self.cpp_info.libs.append('rpcrt4')
        else:
            self.cpp_info.libs = ['czmq']
        if not self.options.shared:
            self.cpp_info.defines.append('CZMQ_STATIC')
