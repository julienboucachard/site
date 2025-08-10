bl_info = {
    "name": "Node to Python",
    "author": "Jules",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Node Editor > Sidebar > Node to Python",
    "description": "Converts a node tree to Python code",
    "warning": "",
    "wiki_url": "",
    "category": "Node",
}

import bpy

# Properties to store the generated code
class NodeToPythonProperties(bpy.types.PropertyGroup):
    """Properties to store the generated Python code."""
    generated_code: bpy.props.StringProperty(
        name="Generated Code",
        description="The generated Python code from the node tree",
        default="",
    )

# Operator to trigger the conversion
class NODE_OT_node_to_python(bpy.types.Operator):
    """Operator that converts the active node tree to Python code."""
    bl_idname = "node.to_python"
    bl_label = "Convert to Python"

    def execute(self, context):
        space = context.space_data
        node_tree = space.node_tree

        if not node_tree:
            self.report({'ERROR'}, "No active node tree found.")
            return {'CANCELLED'}

        props = context.scene.node_to_python_props
        props.generated_code = self.generate_python_code(node_tree)
        return {'FINISHED'}

    def generate_python_code(self, node_tree):
        """
        Generates Python code from a given node tree.

        This function traverses the nodes and links of the node tree and
        generates Python code to recreate the same node setup.

        Args:
            node_tree (bpy.types.NodeTree): The node tree to convert.

        Returns:
            str: The generated Python code as a string.
        """

        lines = []
        lines.append(f"# Code for Node Tree '{node_tree.name}'")
        lines.append("import bpy")
        lines.append("")
        lines.append("# Get the node tree")
        lines.append(f"node_tree = bpy.data.node_groups.get('{node_tree.name}')")
        lines.append("if not node_tree:")
        lines.append(f"    node_tree = bpy.data.node_groups.new(name='{node_tree.name}', type='{node_tree.bl_idname}')")
        lines.append("")
        lines.append("# Get nodes and links")
        lines.append("nodes = node_tree.nodes")
        lines.append("links = node_tree.links")
        lines.append("")
        lines.append("# Clear existing nodes")
        lines.append("for node in nodes:")
        lines.append("    nodes.remove(node)")
        lines.append("")

        node_vars = {}

        # --- NODES ---
        lines.append("# --- NODES ---")
        for node in node_tree.nodes:
            node_var = node.name.lower().replace(" ", "_").replace(".", "_")
            if node_var in __import__("keyword").kwlist:
                node_var += "_"
            node_vars[node.name] = node_var

            lines.append(f"{node_var} = nodes.new(type='{node.bl_idname}')")
            lines.append(f"{node_var}.name = '{node.name}'")
            lines.append(f"{node_var}.location = ({node.location.x}, {node.location.y})")
            lines.append(f"{node_var}.width = {node.width}")
            lines.append(f"{node_var}.height = {node.height}")

            for input_socket in node.inputs:
                if not input_socket.is_linked and hasattr(input_socket, 'default_value'):
                    value = repr(input_socket.default_value)
                    # For colors and vectors, repr() gives a long output, so we format it
                    if hasattr(input_socket.default_value, 'r'): # Color
                        value = f"({input_socket.default_value.r:.4f}, {input_socket.default_value.g:.4f}, {input_socket.default_value.b:.4f}, {input_socket.default_value.a:.4f})"
                    elif hasattr(input_socket.default_value, 'w'): # Vector4D
                        value = f"({input_socket.default_value.x:.4f}, {input_socket.default_value.y:.4f}, {input_socket.default_value.z:.4f}, {input_socket.default_value.w:.4f})"
                    elif hasattr(input_socket.default_value, 'z'): # Vector3D
                        value = f"({input_socket.default_value.x:.4f}, {input_socket.default_value.y:.4f}, {input_socket.default_value.z:.4f})"
                    elif hasattr(input_socket.default_value, 'y'): # Vector2D
                        value = f"({input_socket.default_value.x:.4f}, {input_socket.default_value.y:.4f})"

                    lines.append(f"{node_var}.inputs['{input_socket.name}'].default_value = {value}")

            lines.append("")

        # --- LINKS ---
        lines.append("# --- LINKS ---")
        for link in node_tree.links:
            from_node_var = node_vars[link.from_node.name]
            to_node_var = node_vars[link.to_node.name]
            lines.append(f"links.new({from_node_var}.outputs['{link.from_socket.name}'], {to_node_var}.inputs['{link.to_socket.name}'])")

        return "\n".join(lines)

# Panel to display the UI
class NODE_PT_node_to_python(bpy.types.Panel):
    """Panel to display the UI for the Node to Python add-on."""
    bl_label = "Node to Python"
    bl_idname = "NODE_PT_node_to_python"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        props = context.scene.node_to_python_props

        layout.operator(NODE_OT_node_to_python.bl_idname, text="Generate Code")
        layout.prop(props, "generated_code", text="")

classes = (
    NodeToPythonProperties,
    NODE_OT_node_to_python,
    NODE_PT_node_to_python,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.node_to_python_props = bpy.props.PointerProperty(type=NodeToPythonProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.node_to_python_props

if __name__ == "__main__":
    register()
