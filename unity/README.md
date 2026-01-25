# Unity WebXR Integration for Frames

This folder is where you'll place your Unity WebGL build for AR/VR features.

## Setup Instructions

### 1. Create Unity Project

1. Open Unity Hub and create a new 3D project
2. Name it "FramesAR" or similar
3. Use Unity 2022.3 LTS or later (recommended for WebXR)

### 2. Install Required Packages

Open Package Manager (Window > Package Manager) and install:

- **WebXR Export** - For WebXR support
  - Add via git URL: `https://github.com/AwareXR/WebXR-Export.git`
- **XR Interaction Toolkit** - For interactions
- **Newtonsoft JSON** - For data parsing

### 3. Configure WebXR Settings

1. Go to Edit > Project Settings > XR Plug-in Management
2. Select "WebXR" for the WebGL platform
3. Configure WebXR settings:
   - Enable "VR Supported"
   - Enable "AR Supported" (if available)

### 4. Create Required Scripts

Create a `GameManager.cs` script to receive data from Vue:

```csharp
using UnityEngine;
using System.Runtime.InteropServices;

public class GameManager : MonoBehaviour
{
    [DllImport("__Internal")]
    private static extern void SendToVue(string message);

    public static GameManager Instance { get; private set; }

    void Awake()
    {
        Instance = this;
    }

    // Called from Vue via SendMessage
    public void ReceiveSceneData(string jsonData)
    {
        Debug.Log("Received data from Vue: " + jsonData);
        // Parse JSON and set up scene
        SceneData data = JsonUtility.FromJson<SceneData>(jsonData);
        SetupScene(data);
    }

    void SetupScene(SceneData data)
    {
        // Load wall image as texture
        // Create frame objects at specified positions
        // Set up AR tracking
    }

    public void SendMessageToVue(string type, string data)
    {
        #if UNITY_WEBGL && !UNITY_EDITOR
        string message = JsonUtility.ToJson(new { type = type, data = data });
        SendToVue(message);
        #endif
    }
}

[System.Serializable]
public class SceneData
{
    public int wallId;
    public string wallImage;
    public WallDimensions wallDimensions;
    public FramePlacement[] framePlacements;
}

[System.Serializable]
public class WallDimensions
{
    public float width;
    public float height;
}

[System.Serializable]
public class FramePlacement
{
    public int frame_id;
    public Position position;
    public Rotation rotation;
    public float scale;
}

[System.Serializable]
public class Position
{
    public float x;
    public float y;
    public float z;
}

[System.Serializable]
public class Rotation
{
    public float x;
    public float y;
    public float z;
}
```

### 5. Create the jslib Plugin

Create `Assets/Plugins/WebGL/VueBridge.jslib`:

```javascript
mergeInto(LibraryManager.library, {
    SendToVue: function(message) {
        var messageStr = UTF8ToString(message);
        if (window.unityToVue) {
            window.unityToVue(messageStr);
        }
    }
});
```

### 6. Build Settings

1. Go to File > Build Settings
2. Select WebGL platform
3. Click "Player Settings"
4. Configure:
   - **Compression Format**: Gzip or Brotli
   - **Publishing Settings**: Enable "Decompression Fallback"
   - **Resolution and Presentation**: Set template to "Minimal"

### 7. Build and Deploy

1. Click "Build" in Build Settings
2. Choose the output folder
3. After build completes, copy the following files to `/frontend/public/unity/`:
   - `Build.data` (or `Build.data.gz`)
   - `Build.framework.js` (or `Build.framework.js.gz`)
   - `Build.wasm` (or `Build.wasm.gz`)
   - `Build.loader.js`

### 8. File Structure

After copying, your folder should look like:

```
frontend/public/unity/
├── Build.data.gz
├── Build.framework.js.gz
├── Build.loader.js
├── Build.wasm.gz
└── StreamingAssets/   (if you have streaming assets)
```

## Scene Setup Recommendations

### Wall Display
- Create a large plane to display the wall image
- Use a shader that supports texture mapping
- Scale based on received wall dimensions

### Frame Objects
- Create prefabs for different frame sizes
- Use instancing for performance
- Apply picture textures dynamically

### AR Features
- Implement plane detection for real-world surfaces
- Allow users to tap to place virtual frames
- Support gesture controls (pinch to scale, drag to move)

### Performance Tips
- Use object pooling for frames
- Implement LOD (Level of Detail) for complex frames
- Optimize textures for mobile

## Communication Protocol

### Vue to Unity (via SendMessage)

```javascript
// Send scene data
unityInstance.SendMessage('GameManager', 'ReceiveSceneData', JSON.stringify({
  wallId: 1,
  wallImage: 'path/to/wall.jpg',
  wallDimensions: { width: 300, height: 250 },
  framePlacements: [...]
}));
```

### Unity to Vue (via jslib)

```csharp
// In Unity C#
SendMessageToVue("frameMoved", JsonUtility.ToJson(new {
  frameId = 1,
  position = new { x = 0.5, y = 1.2, z = 0 }
}));
```

## Troubleshooting

### Build fails
- Ensure all packages are compatible with WebGL
- Check for unsupported .NET features

### WebXR not working
- Test in a WebXR-compatible browser (Chrome, Firefox)
- Ensure HTTPS is used (required for WebXR)
- Check browser console for errors

### Communication issues
- Verify `window.unityToVue` is defined before Unity loads
- Check for JSON parsing errors
- Use browser dev tools to debug

## Resources

- [Unity WebGL Documentation](https://docs.unity3d.com/Manual/webgl.html)
- [WebXR Export Package](https://github.com/AwareXR/WebXR-Export)
- [Three.js (Alternative)](https://threejs.org/) - If you want pure web-based 3D
