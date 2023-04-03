@REM c:\p4\audio2face\run_avatar.bat ^
%localappdata%\ov\pkg\audio2face-2023.1.0-beta.4\avatar.kit.bat ^
    --enable omni.services.transport.server.http ^
    --enable omni.kit.tool.asset_exporter ^
    --enable omni.avatar.livelink ^
    --enable omni.avatar.ui.livelink ^
    --/app/renderer/sleepMsOutOfFocus=0 ^
    --/app/renderer/sleepMsOutOfFocus=0 ^
    --/app/asyncRendering=false ^
    --/rtx/reflections/enabled=false ^
    --/rtx/translucency/enabled=false ^
    --/rtx/post/lensFlares/enabled=false ^
    --/rtx/post/dof/enabled=false ^
    --/rtx/indirectDiffuse/enabled=false ^
    %*