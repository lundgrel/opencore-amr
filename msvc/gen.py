import re,sys,uuid,os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def gen(name, mk, defs_extra, extra_inc, srcvars):
    txt=open(os.path.join(root,mk)).read().replace(chr(92)+chr(10),' ')
    # sources (including conditional ones), skip comment lines
    srcs=[]
    for line in txt.splitlines():
        if line.lstrip().startswith('#'): continue
        for m in re.finditer(r'(\$\((\w+)\)/)?([\w]+\.cpp)',line):
            srcs.append((m.group(2),m.group(3)))
    out=[]
    for var,f in srcs:
        if var is None: p='../'+os.path.dirname(mk)+'/'+f
        else: p='../'+srcvars[var]+'/'+f
        out.append(p.replace('/',chr(92)))
    # amrnb encoder/decoder have same-named files (div_32, l_abs, vad1): object name clash
    objs={}
    items=[]
    for p in out:
        b=os.path.basename(p)[:-4]
        objs[b]=objs.get(b,0)+1
        items.append((p,b))
    seen={}
    cl=[]
    for p,b in items:
        seen[b]=seen.get(b,0)+1
        if objs[b]>1:
            cl.append(f'    <ClCompile Include="{p}"><ObjectFileName>$(IntDir){os.path.basename(os.path.dirname(os.path.dirname(p)))}_{b}.obj</ObjectFileName></ClCompile>')
        else: cl.append(f'    <ClCompile Include="{p}" />')
    inc=';'.join(x.replace('/',chr(92)) for x in extra_inc)
    cfgs=[(c,p) for c in('Debug','Release') for p in('Win32','x64')]
    s='<?xml version="1.0" encoding="utf-8"?>\n<Project DefaultTargets="Build" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\n  <ItemGroup Label="ProjectConfigurations">\n'
    for c,p in cfgs:
        s+=f'    <ProjectConfiguration Include="{c}|{p}"><Configuration>{c}</Configuration><Platform>{p}</Platform></ProjectConfiguration>\n'
    s+=f'''  </ItemGroup>
  <PropertyGroup Label="Globals">
    <ProjectGuid>{{{str(uuid.uuid5(uuid.NAMESPACE_DNS,name)).upper()}}}</ProjectGuid>
    <RootNamespace>{name}</RootNamespace>
    <WindowsTargetPlatformVersion>10.0</WindowsTargetPlatformVersion>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.Default.props" />
  <PropertyGroup Label="Configuration">
    <ConfigurationType>StaticLibrary</ConfigurationType>
    <PlatformToolset>v143</PlatformToolset>
    <CharacterSet>Unicode</CharacterSet>
  </PropertyGroup>
  <PropertyGroup Condition="'$(Configuration)'=='Debug'" Label="Configuration"><UseDebugLibraries>true</UseDebugLibraries></PropertyGroup>
  <PropertyGroup Condition="'$(Configuration)'=='Release'" Label="Configuration"><UseDebugLibraries>false</UseDebugLibraries></PropertyGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.props" />
  <PropertyGroup>
    <OutDir>$(SolutionDir)bin\$(Platform)\$(Configuration)\</OutDir>
    <IntDir>$(SolutionDir)obj\$(ProjectName)\$(Platform)\$(Configuration)\</IntDir>
    <TargetName>{name}</TargetName>
  </PropertyGroup>
  <ItemDefinitionGroup>
    <ClCompile>
      <WarningLevel>Level3</WarningLevel>
      <AdditionalIncludeDirectories>{inc};%(AdditionalIncludeDirectories)</AdditionalIncludeDirectories>
      <PreprocessorDefinitions>{defs_extra}_CRT_SECURE_NO_WARNINGS;_LIB;%(PreprocessorDefinitions)</PreprocessorDefinitions>
      <DisableSpecificWarnings>4244;4267;4018;4146;4305;4309;4996;%(DisableSpecificWarnings)</DisableSpecificWarnings>
      <MultiProcessorCompilation>true</MultiProcessorCompilation>
      <DebugInformationFormat>ProgramDatabase</DebugInformationFormat>
      <ProgramDataBaseFileName>$(OutDir)$(TargetName).pdb</ProgramDataBaseFileName>
    </ClCompile>
  </ItemDefinitionGroup>
  <ItemDefinitionGroup Condition="'$(Configuration)'=='Debug'">
    <ClCompile><RuntimeLibrary>MultiThreadedDebug</RuntimeLibrary><Optimization>Disabled</Optimization><PreprocessorDefinitions>_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions></ClCompile>
  </ItemDefinitionGroup>
  <ItemDefinitionGroup Condition="'$(Configuration)'=='Release'">
    <ClCompile><RuntimeLibrary>MultiThreaded</RuntimeLibrary><Optimization>MaxSpeed</Optimization><PreprocessorDefinitions>NDEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions></ClCompile>
  </ItemDefinitionGroup>
  <ItemGroup>
'''+'\n'.join(cl)+'''
  </ItemGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />
</Project>
'''
    open(os.path.join(root,'msvc',name+'.vcxproj'),'w').write(s)
    return str(uuid.uuid5(uuid.NAMESPACE_DNS,name)).upper()
A='opencore/codecs_v2/audio/gsm_amr'
nb=A+'/amr_nb'
g1=gen('opencore-amrnb','amrnb/Makefile.am','',
  ['../oscl','../'+nb+'/dec/src','../'+nb+'/common/include','../'+nb+'/dec/include','../'+A+'/common/dec/include','../'+nb+'/enc/src'],
  {'DEC_SRC_DIR':nb+'/dec/src','ENC_SRC_DIR':nb+'/enc/src','COMMON_SRC_DIR':nb+'/common/src'})
wb=A+'/amr_wb'
g2=gen('opencore-amrwb','amrwb/Makefile.am','',
  ['../oscl','../'+wb+'/dec/src','../'+wb+'/dec/include','../'+A+'/common/dec/include'],
  {'DEC_SRC_DIR':wb+'/dec/src'})
sln='Microsoft Visual Studio Solution File, Format Version 12.00\n# Visual Studio Version 17\n'
for n,g in(('opencore-amrnb',g1),('opencore-amrwb',g2)):
    sln+=f'Project("{{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}") = "{n}", "{n}.vcxproj", "{{{g}}}"\nEndProject\n'
sln+='Global\n\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n'
for c in('Debug','Release'):
    for p in('Win32','x64'): sln+=f'\t\t{c}|{p} = {c}|{p}\n'
sln+='\tEndGlobalSection\n\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n'
for g in(g1,g2):
    for c in('Debug','Release'):
        for p in('Win32','x64'):
            sln+=f'\t\t{{{g}}}.{c}|{p}.ActiveCfg = {c}|{p}\n\t\t{{{g}}}.{c}|{p}.Build.0 = {c}|{p}\n'
sln+='\tEndGlobalSection\nEndGlobal\n'
open(os.path.join(root,'msvc','opencore-amr.sln'),'w').write(sln)
