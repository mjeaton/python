import os
import stat
import shutil

"""
This will find all .vssscs and .vspscc files and remove them. They contain outdated source code control information.
It will then open each .sln file and remove old TFS bindings.

The .vssscs and .vspscc files can just be deleted, but the solution file is a bit more complicated. Within the solution file, there is a block that needs to be removed.
An example solution file:

Microsoft Visual Studio Solution File, Format Version 11.00
# Visual Studio 2010
Project("{BEF9B85E-E7F7-4F6C-8B60-8207CBAD7746}") = "ProjectName", "ProjectName.csproj", "{F8C806B6-DC73-4AA3-8E20-931895A01DB0}"
EndProject

Global
    GlobalSection(TeamFoundationVersionControl) = preSolution
        SccNumberOfProjects = 2
        SccEnterpriseProvider = {5D5C1553-148B-4127-A5A9-D45B0C12AEDB}
        SccTeamFoundationServer = http://blahblahblah
        SccLocalPath = .
    EndGlobalSection
    GlobalSection(SolutionConfigurationPlatforms) = preSolution
        Debug|x86 = Debug|x86
        Release|x86 = Release|x86
    EndGlobalSection
EndGlobal

"""

def cleanup():

    rootdir = "<full path for the items you want to process>" 

    print("Removing all VSTS-related files.")
    filesRemoved = remove_files(rootdir)
    print("{0} files have been deleted.".format(filesRemoved))
    print()

    print("Automatically removing the 'GlobalSection(TeamFoundationVersionControl)' section from all .sln files")
    solutionsUpdated = fixup_solution_files(rootdir)
    print("{0} solution files have been updated.".format(solutionsUpdated))

def fixup_solution_files(root):
    sectionStart = "GlobalSection(TeamFoundationVersionControl) = preSolution"
    sectionEnd = "EndGlobalSection"
    
    solutionFilesUpdated = 0
    for subdir, _, files in os.walk(root):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext == ".sln":
                solutionFile = os.path.join(subdir, file)
                newSolutionFile = solutionFile + ".new"
                oldSolutionFile = solutionFile + ".old"

                inSection = False
        
                # looks in the solution file to see if there's anything to remove
                doFile = sectionStart in open(solutionFile, 'r').read()

                # if there are old TFS bindings, remove them after making a
                if doFile:
                    solutionFilesUpdated += 1
                    os.chmod(solutionFile, stat.S_IWRITE)
                    with open(newSolutionFile, 'w') as outfile:
                        with open(solutionFile, 'r') as file:
                            for x in file:
                                if x.strip() == sectionStart:
                                    inSection = True
                                elif inSection and x.strip() == sectionEnd:
                                    inSection = False
                                else:
                                    if not inSection:
                                        outfile.write(x)
                
                if os.path.isfile(newSolutionFile):
                    shutil.copyfile(solutionFile, oldSolutionFile)
                    shutil.copyfile(newSolutionFile, solutionFile)
                    os.remove(newSolutionFile)

    return solutionFilesUpdated

def remove_files(root):
    extensionsToDelete = ['.vssscc', '.vspscc']
    filesDeleted = 0

    for subdir, _, files in os.walk(root):
        for file in files:
            _, ext = os.path.splitext(file)
            fileToRemoveOrEdit = os.path.join(subdir, file)
            if ext in extensionsToDelete:
                try:
                    os.chmod(fileToRemoveOrEdit, stat.S_IWRITE)
                    os.remove(fileToRemoveOrEdit)
                    filesDeleted += 1 
                except OSError as oe:
                    print("Error deleting '{0}' because {1}".format(fileToRemoveOrEdit, oe)) 

    return filesDeleted

if __name__ == '__main__':
    cleanup()
