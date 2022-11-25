import omni.ext
import omni.ui as ui
import omni.usd
import omni.kit
from pxr import UsdGeom, Gf, Usd, Sdf

# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print(f"[omni.hello.world] some_public_function was called with {x}")
    return x ** x


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[omni.hello.world] MyExtension startup")

        self._selected_prim = None

        # C:\p4\one-minute-omniverse\exploded-view-extension\app\kit\extscore\omni.usd\omni\usd\_usd.pyi
        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                def on_explode():
                    ctx = omni.usd.get_context()
                    stage = ctx.get_stage()
                    selection = ctx.get_selection().get_selected_prim_paths()
                    if not selection:
                        return

                    path = selection[0]
                    # https://graphics.pixar.com/usd/release/api/class_usd_stage.html#a6ceb556070804b712c01a7968f925735
                    self._selected_prim = stage.GetPrimAtPath(path)
                    
                    for prim in self._selected_prim.GetChildren():
                        if not prim.IsA(UsdGeom.Mesh):
                            continue
                        print(prim)
                        prim_path = prim.GetPrimPath().pathString
                        # local_transform = omni.usd.get_local_transform_SRT(prim)
                        # translation: Gf.Vec3d = local_transform[3]
                        # print(translation)
                        
                        aabb_min, aabb_max = ctx.compute_path_world_bounding_box(prim_path)
                        center = Gf.Vec3f()
                        center[0] = (aabb_min.x + aabb_max.x) / 2
                        center[1] = (aabb_min.y + aabb_max.y) / 2
                        center[2] = (aabb_min.z + aabb_max.z) / 2
                        
                        trans = Gf.Vec3d()
                        trans[0] = center[0] * self._scale_x.model.get_value_as_float()
                        trans[1] = center[1] * self._scale_y.model.get_value_as_float()
                        trans[2] = center[2] * self._scale_z.model.get_value_as_float()
                        omni.kit.commands.execute("TransformPrimSRTCommand", path=prim_path, new_translation=trans)

                        
                def on_reset():
                    if not self._selected_prim:
                        return

                    for prim in self._selected_prim.GetChildren():
                        if not prim.IsA(UsdGeom.Mesh):
                            continue
                        prim_path = prim.GetPrimPath().pathString
                        omni.kit.commands.execute("TransformPrimSRTCommand", path=prim_path, new_translation=Gf.Vec3d())

                on_reset()

                with ui.HStack():
                    with ui.VStack():
                        self._scale_x = ui.FloatSlider(min=0, max=2)
                        self._scale_y = ui.FloatSlider(min=0, max=2)
                        self._scale_z = ui.FloatSlider(min=0, max=2)
                    ui.Button("Explode", clicked_fn=on_explode)
                    ui.Button("Reset", clicked_fn=on_reset)

    def on_shutdown(self):
        print("[omni.hello.world] MyExtension shutdown")
