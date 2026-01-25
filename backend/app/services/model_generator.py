"""3D model generation for picture frames."""
import os
import numpy as np

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False


def generate_frame_model(frame_id, width_cm, height_cm, depth_cm, output_folder, picture_path=None):
    """
    Generate a simple 3D box/frame model.

    Args:
        frame_id: Unique identifier for the frame
        width_cm: Frame width in centimeters
        height_cm: Frame height in centimeters
        depth_cm: Frame depth in centimeters
        output_folder: Folder to save the model
        picture_path: Optional path to picture for texture

    Returns:
        Path to the generated model file, or None if generation failed
    """
    if not TRIMESH_AVAILABLE:
        print("trimesh not available, skipping model generation")
        return _generate_simple_obj(frame_id, width_cm, height_cm, depth_cm, output_folder)

    try:
        # Convert cm to meters for standard 3D units
        width = width_cm / 100.0
        height = height_cm / 100.0
        depth = depth_cm / 100.0

        # Create a simple box mesh representing the frame
        box = trimesh.creation.box(extents=[width, height, depth])

        # Center the box at origin
        box.vertices -= box.centroid

        # Export as GLB (binary glTF)
        output_path = os.path.join(output_folder, f"frame_{frame_id}.glb")
        box.export(output_path, file_type='glb')

        return output_path

    except Exception as e:
        print(f"Error generating 3D model: {e}")
        return _generate_simple_obj(frame_id, width_cm, height_cm, depth_cm, output_folder)


def _generate_simple_obj(frame_id, width_cm, height_cm, depth_cm, output_folder):
    """
    Generate a simple OBJ file without external dependencies.

    Args:
        frame_id: Unique identifier for the frame
        width_cm: Frame width in centimeters
        height_cm: Frame height in centimeters
        depth_cm: Frame depth in centimeters
        output_folder: Folder to save the model

    Returns:
        Path to the generated OBJ file
    """
    # Convert to meters and half-extents
    w = (width_cm / 100.0) / 2
    h = (height_cm / 100.0) / 2
    d = (depth_cm / 100.0) / 2

    # Define the 8 vertices of a box
    vertices = [
        (-w, -h, -d),  # 0: back bottom left
        (w, -h, -d),   # 1: back bottom right
        (w, h, -d),    # 2: back top right
        (-w, h, -d),   # 3: back top left
        (-w, -h, d),   # 4: front bottom left
        (w, -h, d),    # 5: front bottom right
        (w, h, d),     # 6: front top right
        (-w, h, d),    # 7: front top left
    ]

    # Define the 6 faces (using 1-indexed vertices for OBJ format)
    faces = [
        (1, 2, 3, 4),  # back
        (5, 8, 7, 6),  # front
        (1, 5, 6, 2),  # bottom
        (3, 7, 8, 4),  # top
        (1, 4, 8, 5),  # left
        (2, 6, 7, 3),  # right
    ]

    # UV coordinates for texture mapping
    uvs = [
        (0, 0),
        (1, 0),
        (1, 1),
        (0, 1),
    ]

    output_path = os.path.join(output_folder, f"frame_{frame_id}.obj")

    try:
        with open(output_path, 'w') as f:
            f.write(f"# Frame model generated for frame {frame_id}\n")
            f.write(f"# Dimensions: {width_cm}cm x {height_cm}cm x {depth_cm}cm\n\n")

            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            f.write("\n")

            # Write UV coordinates
            for uv in uvs:
                f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

            f.write("\n")

            # Write normals (6 face normals)
            normals = [
                (0, 0, -1),  # back
                (0, 0, 1),   # front
                (0, -1, 0),  # bottom
                (0, 1, 0),   # top
                (-1, 0, 0),  # left
                (1, 0, 0),   # right
            ]
            for n in normals:
                f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")

            f.write("\n")

            # Write faces with texture coordinates and normals
            for i, face in enumerate(faces):
                # OBJ format: f v/vt/vn
                f.write(f"f {face[0]}/1/{i+1} {face[1]}/2/{i+1} {face[2]}/3/{i+1} {face[3]}/4/{i+1}\n")

        return output_path

    except Exception as e:
        print(f"Error generating OBJ: {e}")
        return None


def generate_frame_with_border(frame_id, inner_width_cm, inner_height_cm,
                                border_width_cm, depth_cm, output_folder):
    """
    Generate a picture frame with a border/mat around the picture area.

    Args:
        frame_id: Unique identifier for the frame
        inner_width_cm: Width of the picture area
        inner_height_cm: Height of the picture area
        border_width_cm: Width of the frame border
        depth_cm: Depth of the frame
        output_folder: Folder to save the model

    Returns:
        Path to the generated model file
    """
    outer_width = inner_width_cm + (2 * border_width_cm)
    outer_height = inner_height_cm + (2 * border_width_cm)

    # For now, generate a simple box with the outer dimensions
    # A more complex version would create a hollow frame
    return generate_frame_model(
        frame_id,
        outer_width,
        outer_height,
        depth_cm,
        output_folder
    )
