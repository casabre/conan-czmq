# -*- coding: utf-8 -*-
import os
from conans import ConanFile, tools, CMake


class CZMQConan(ConanFile):
    name = "czmq"
    version = "4.1.0"
    url = "https://github.com/bincrafters/conan-czmq"
    homepage = "https://github.com/zeromq/czmq"
    description = "High-level C binding for ØMQ"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "MPL-2.0"
    exports = ["LICENSE.md"]
    topics = ("conan", "czmq", "zmq", "zeromq", "message-queue", "asynchronous")
    exports_sources = ['CMakeLists.txt', 'czmq.diff']
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "lz4": [True, False], "uuid": [True, False]}
    default_options = {"shared": False, "fPIC": True, "lz4": True, "uuid": True}
    generators = ['cmake']
    _source_subfolder = "source_subfolder"

    def configure(self):
        if self.settings.compiler == 'Visual Studio':
            del self.options.fPIC

    def build_requirements(self):
        if not tools.which("ninja"):
            self.build_requires.add('ninja_installer/1.8.2@bincrafters/stable')

    def requirements(self):
        self.requires.add('zmq/4.2.2@bincrafters/stable')
        if self.options.lz4:
            self.requires.add('lz4/1.8.3@bincrafters/stable')
        if self.options.uuid:
            self.requires.add('libuuid/1.0.3@bincrafters/stable')

    def source(self):
        sha256 = "2e87c19988d1168b70d7ec0fdce79aba4e92a6330959c3a2576c72b319acb478"
        tools.get("{0}/archive/v{1}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        generator = 'Ninja' if self.settings.compiler == "Visual Studio" else None
        cmake = CMake(self, generator=generator)
        cmake.definitions["CZMQ_BUILD_SHARED"] = self.options.shared
        cmake.definitions["CZMQ_BUILD_STATIC"] = not self.options.shared
        cmake.configure()
        return cmake

    def _build_cmake(self):
        cmake = self._configure_cmake()
        cmake.build()

    def build(self):
        tools.patch(base_path=self._source_subfolder, patch_file="czmq.diff")
        if self.settings.compiler == 'Visual Studio':
            with tools.vcvars(self.settings, force=True, filter_known_paths=False):
                self._build_cmake()
        else:
            self._build_cmake()

    def package(self):
        self.copy(pattern="LICENSE", src=self._source_subfolder, dst='licenses')
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        if self.settings.compiler == 'Visual Studio':
            self.cpp_info.libs = ['czmq' if self.options.shared else 'libczmq']
            self.cpp_info.libs.append('rpcrt4')
        else:
            self.cpp_info.libs = ['czmq']
            if self.settings.os == "Linux":
                self.cpp_info.libs.extend(["pthread", "m"])
        if not self.options.shared:
            self.cpp_info.defines.append('CZMQ_STATIC')
