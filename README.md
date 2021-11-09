# **ODB :arrow_right: VTK utility**

> **:bulb: Info -** this is an utility to read an Abaqus odb and convert the mesh and field data into a vtk format. This is useful to convert data directly on the HPC where the odb is generated for remote visualization through Paraview.

## **Usage**

- **_`Python 2`_** : for older versions of pvpython (e.g. 5.2.0). Check your paraview installation.
- **_`Python 3`_** : works in more recent versions of pvpython (e.g. 5.7.0+).
- The different versions differ only on the `vtk` side of things, specifically on `vtkTools` and how printing to console is handled. the `odb` side of things needs to run in the abaqus python environment which is python 2.
- `Note`: The `odbExtractor` script will attempt to run two `pvpython` commands in the end. In some systems this fails. Steps 2 and 3 below are only needed in those systems where the command execution from python is blocked.

```batch
abaqus cae noGui=odbExtractor.py -- -o <odbName>.odb -r <requestName>.json -f all -d true
```

[optional - see note above]

```batch
pvpython vtkFromOdb.py <odbName>.odb
```

[optional - see note above]

```batch
pvpython vtkTimeSeriesBuilder.py <odbName>.odb
```

### **Environment and dependencies**

- Abaqus installation: tested on Abaqus 2019;
- Paraview installation with pvpython: tested on paraview 5.2.0, 5.8.0 and 5.9.1;

### **Execution options**

- **_-o_** (--odb) : `odbName.odb`

  - specify the name of the odb to extract data from

- **_-r_** (--request): `requestName.json`

  - specify the name of the json file outlining the frames to be extracted. This is specified in the `frameIdList` as a list of integer pairs `[step number, frame number]`. Index -1 can be used to specify last entry.

  ```json
  {
    "frameIdList": [
      [1, 1],
      [1, 2],
      [2, -1],
      [-1, 3]
    ]
  }
  ```

- **_-f_** (--fields): `disp` or `all` (default: `all`)

  - specify the fields to be extracted. Currently supported options are displacement only ("disp") or every supported field ("all" or anyother string value). Currently supported fields are:

- **_-d_** (--duplicate): `true` or `false` (default: `true`)

  - specify whether to duplicate the odb leaving a copy intact to avoid data loss in case of odb corruption.

### **Features available**

Current feature set is limited, but expanding:

- supported fields:

  ```python
  scalar  = ['SDV', 'FV', 'UVARM']
  vector  = ['U']
  tensor  = ['S', 'LE']
  contact = ['CSDMG']
  ```

- supported elements: `['SC8R', 'SC6R', 'CSS8', 'S4R']`
- supported stress state: `plane stress` with the following invariants and components `['11', '22', '33', '12', 'MAX_INPLANE_PRINCIPAL']`
- filters / post-processing : currently only envelopes are computed for all tensor fields.
- vector fields are stored with the respective components as `vtkFloatArray` with 3 components - Paraview can make use of this for deformed representations and so on.
- frame times are saved and a seperate `PVD` file is created with the time series data containing the `vtkMultiBlockDataSets`;

### **Expansion**

- Post processing steps can be added in `odbFieldExtractor`;
- Element types can be added in `odbMeshExtractor` - note that for different stress states changes need to be made in `odbFieldExtractor` and for different element geometries (other than hex, wedge and quad) changes need to be made to `vtkGridBuilder`
