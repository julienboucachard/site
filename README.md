# Node to Python Blender Add-on

This add-on for Blender converts a shader or geometry node tree to Python code. This allows you to easily reuse your node setups in other projects or share them with others.

## Installation

1.  Download the `node_to_python.py` file.
2.  Open Blender and go to `Edit > Preferences > Add-ons`.
3.  Click the `Install...` button and select the `node_to_python.py` file.
4.  Enable the add-on by checking the box next to "Node: Node to Python".

## How to Use

1.  Open the Shader Editor or Geometry Node Editor.
2.  In the sidebar (press `N` to open), you will find a new tab called "Tool".
3.  Inside the "Tool" tab, there is a panel named "Node to Python".
4.  Select the object with the material or geometry nodes you want to convert.
5.  Click the "Generate Code" button.
6.  The generated Python code will appear in the text box below the button.
7.  You can copy the code from the text box and save it to a `.py` file or paste it into the Blender Text Editor to run it.

## How it Works

The add-on works by traversing the active node tree and generating Python code for each node and link. It creates a variable for each node and then sets its properties and default values. Finally, it creates the links between the nodes.

## Limitations

*   The generated code assumes that the node tree is a `ShaderNodeTree` or `GeometryNodeTree`. You may need to manually change the type if you are using a different type of node tree.
*   The add-on does not yet support all types of node properties (e.g., custom properties).
*   The generated variable names for the nodes are based on their names in the node tree. If you have nodes with the same name, this might cause issues. It's recommended to use unique names for your nodes.
