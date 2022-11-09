# How to get started
This project has only been tested and run in vscode, which the following instructions will reflect as well.

To use build and run this example the following steps need to be carried out:
1. Run the <b>dotnet restore</b> command in the folder containing the NBAPrediction.csproj file.
2. If debugging does not start, check the C# extension version. There is some issue with 1.25.0 version causing the debugging to fail due to Omnisharp server not starting, this is solved by downgrading the extension to 1.24.4.
3. If the debugging complains about settings not being configured, first let vscode generate configuration for .NetCore3.1. If that does not help, update the launch.json and tasks.json in the NBAPrediction\.vscode folder (or similar in a different project) to look like the below.
## launch.json
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": ".NET Core Launch (console)",
            "type": "coreclr",
            "request": "launch",
            "preLaunchTask": "build",
            "program": "${workspaceFolder}/bin/Debug/netcoreapp3.1/NBAPrediction.dll",
            "args": [],
            "cwd": "${workspaceFolder}",
            "console": "internalConsole",
            "stopAtEntry": false
        },
        {
            "name": ".NET Core Attach",
            "type": "coreclr",
            "request": "attach"
        }
    ]
}
```
## tasks.json
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "build",
            "command": "dotnet",
            "type": "process",
            "args": [
                "build",
                "${workspaceFolder}/NBAPrediction.csproj",
                "/property:GenerateFullPaths=true",
                "/consoleloggerparameters:NoSummary"
            ],
            "problemMatcher": "$msCompile"
        },
        {
            "label": "publish",
            "command": "dotnet",
            "type": "process",
            "args": [
                "publish",
                "${workspaceFolder}/NBAPrediction.csproj",
                "/property:GenerateFullPaths=true",
                "/consoleloggerparameters:NoSummary"
            ],
            "problemMatcher": "$msCompile"
        },
        {
            "label": "watch",
            "command": "dotnet",
            "type": "process",
            "args": [
                "watch",
                "run",
                "--project",
                "${workspaceFolder}/NBAPrediction.csproj"
            ],
            "problemMatcher": "$msCompile"
        }
    ]
}
```

The above steps are generally necessary whenever you try to run\debug a spark dotnet project in a new docker container.
