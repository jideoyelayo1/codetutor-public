"""Original Stage 22 efficient-ML-systems depth: PyTorch 2.8 CPU checks of devices, precision, layout, export and data partitioning."""
from python_guide_depth import add, task

TORCH = "import torch"
DOCS = 'https://docs.pytorch.org/docs/2.8/'
GEN = DOCS+'generated/'

add('device-contract', 'torch.device: one device decision, applied to model and data',
    DOCS+'tensor_attributes.html#torch-device', [
    "Choose the device once, for example cuda when available and cpu otherwise, and move both the model and every input batch to it. Operations between tensors on different devices raise errors, so the decision must be shared, not repeated ad hoc.",
    "tensor.to(device) returns the same tensor object when it is already on that device with the requested dtype, and a copy otherwise. Code that mutates the result in place can therefore unexpectedly change the original on CPU-only machines.",
    "This lab runs on CPU and verifies the device bookkeeping only. GPU and Apple MPS behaviour, kernel availability and performance require their own hardware validation, which this guide labels separately.",
    "The transfer resolves a device, moves a tensor and a model, and checks that they agree."
    ],
    ("What does x.to('cpu') return when x is already a CPU tensor of the same dtype?",
     "The same tensor object, not a copy.",
     ["Always a new copy.", "None.", "A tensor on the default CUDA device."],
     "to() is a no-op when nothing changes; clone() when an independent copy is required."),
    task("Transfer: share one device decision",
         "data is 'auto' or 'cpu'. Resolve cuda if data is 'auto' and CUDA is available, otherwise cpu. Move a tensor and a Linear(2, 1) to it. Return [tensor and model devices agree, the moved tensor is the original object when on cpu, moved dtype].",
         "device = torch.device('cuda' if torch.cuda.is_available() and data == 'auto' else 'cpu')\nx = torch.tensor([1.0, 2.0])\nmoved = x.to(device)\nmodel = torch.nn.Linear(2, 1).to(device)\nresult = [moved.device.type == next(model.parameters()).device.type, moved is x if device.type == 'cpu' else 'copied', str(moved.dtype)]",
         [('cpu',[True,True,'torch.float32']),('auto',[True,True,'torch.float32']),('cpu',[True,True,'torch.float32'])],
         ("moved = x.to(device)","moved = x.clone()"),
         ["Resolve the device once and reuse it.", "to() returns self when no change is needed.", "Model parameters and inputs must share a device."],
         "On this CPU host both the tensor and the model are on cpu, and to() returns the original tensor object. clone() would always copy, so identity no longer holds.",
         [[False,True,'torch.float32'],[True,False,'torch.float32'],[True,True,'torch.float64']],
         TORCH),
    ("Why decide the device once in a training script?", "So the model and every batch end up on the same device; mixed devices raise errors."))

add('autocast-cpu', 'CPU autocast: which operations run in bfloat16',
    DOCS+'amp.html#cpu-ops-that-can-autocast-to-bfloat16', [
    "torch.autocast(device_type='cpu', dtype=torch.bfloat16) runs eligible operations, such as linear layers and matrix multiplications, in bfloat16, a listed set of numerically sensitive operations runs in float32, and everything else simply follows its inputs' dtype. On CPU, softmax is not on the float32 list, so the softmax of a bfloat16 output stays bfloat16. The policy is per operation, not per tensor.",
    "bfloat16 keeps float32's exponent range but only about three significant decimal digits. Outputs are close to, not equal to, full precision, so compare them with a tolerance and keep losses and accumulations in float32.",
    "Outside the autocast region, the same layer computes in float32 again. Measure accuracy and speed on the target hardware before adopting mixed precision; benefits on CPU vary with the processor.",
    "The transfer runs a linear layer and a softmax under CPU autocast and compares with full precision."
    ],
    ("Inside CPU bfloat16 autocast, what dtype does a Linear layer's output have?",
     "torch.bfloat16, because linear is on the lower-precision list.",
     ["torch.float32 always.", "torch.float16.", "The input's dtype."],
     "Autocast chooses dtypes per operation."),
    task("Transfer: mixed precision with a tolerance",
         "data is a pair of input values. Under CPU bfloat16 autocast, run Linear(2, 1) and a softmax on its output; run the layer again outside autocast. Return [linear dtype, softmax dtype, full-precision dtype, whether outputs agree within 0.05].",
         "layer = torch.nn.Linear(2, 1)\nx = torch.tensor([data], dtype=torch.float32)\nwith torch.autocast(device_type='cpu', dtype=torch.bfloat16):\n    y = layer(x)\n    s = torch.softmax(y, dim=1)\nexact = layer(x)\nresult = [str(y.dtype), str(s.dtype), str(exact.dtype), bool(torch.allclose(y.float(), exact, atol=0.05))]",
         [([1,2],['torch.bfloat16','torch.bfloat16','torch.float32',True]),([0,0],['torch.bfloat16','torch.bfloat16','torch.float32',True]),([-1,0.5],['torch.bfloat16','torch.bfloat16','torch.float32',True])],
         ("dtype=torch.bfloat16):","dtype=torch.bfloat16, enabled=False):"),
         ["Linear layers autocast to bfloat16.", "Unlisted operations, such as CPU softmax here, follow their input dtype.", "Compare low-precision results with a tolerance."],
         'The linear output is bfloat16 under autocast, the softmax inherits that dtype, and the same layer outside the region computes in float32. The two outputs agree within 0.05. Disabling autocast leaves everything in float32.',
         [['torch.float32','torch.float32','torch.float32',True],['torch.bfloat16','torch.float32','torch.float32',True],['torch.bfloat16','torch.bfloat16','torch.bfloat16',True]],
         TORCH),
    ("Why compare autocast outputs with a tolerance?", "bfloat16 keeps only about three significant digits, so results are close but not identical."))

add('numpy-torch-storage', 'torch.from_numpy shares memory; torch.tensor copies',
    GEN+'torch.from_numpy.html#torch.from_numpy', [
    "torch.from_numpy(a) wraps a NumPy array's memory without copying, and tensor.numpy() does the same in the other direction for CPU tensors. Changing one changes the other. The dtype is preserved, so float64 arrays become float64 tensors.",
    "torch.tensor(a) always copies. Use it when the tensor must be independent of later changes to the array, for example when an input buffer is reused for the next batch.",
    "Most models use float32; a float64 tensor from NumPy will either be rejected by a float32 layer or silently slow computation. Convert explicitly with .float() at the boundary.",
    "The transfer modifies a NumPy array after creating shared and copied tensors."
    ],
    ("A tensor was created with torch.from_numpy(a). What happens to it when a[0] is changed?",
     "It changes too, because both share the same memory.",
     ["Nothing; from_numpy copies.", "PyTorch raises an error.", "Only its gradient changes."],
     "Use torch.tensor(a) for an independent copy."),
    task("Transfer: shared and copied conversions",
         "data is a list of numbers. Create a float64 array, a shared tensor via from_numpy, a copied tensor via torch.tensor and a NumPy view via shared.numpy(). Set a[0] = 99 and return [shared, copied, view, shared dtype].",
         "a = np.asarray(data, dtype=np.float64)\nshared = torch.from_numpy(a)\ncopied = torch.tensor(a)\nback = shared.numpy()\na[0] = 99\nresult = [shared.tolist(), copied.tolist(), back.tolist(), str(shared.dtype)]",
         [([1,2],[[99.0,2.0],[1.0,2.0],[99.0,2.0],'torch.float64']),([0],[[99.0],[0.0],[99.0],'torch.float64']),([5,6,7],[[99.0,6.0,7.0],[5.0,6.0,7.0],[99.0,6.0,7.0],'torch.float64'])],
         ("copied = torch.tensor(a)","copied = torch.from_numpy(a)"),
         ["from_numpy and .numpy() share memory.", "torch.tensor copies.", "The NumPy dtype carries over."],
         "The shared tensor and the NumPy view both show 99, while the copy keeps 1. The dtype stays float64. Using from_numpy for the copy would share the change too.",
         [[[1.0,2.0],[1.0,2.0],[99.0,2.0],'torch.float64'],[[99.0,2.0],[99.0,2.0],[99.0,2.0],'torch.float64'],[[99.0,2.0],[1.0,2.0],[99.0,2.0],'torch.float32']],
         TORCH+"\nimport numpy as np"),
    ("How do you get an independent tensor from a NumPy array?", "torch.tensor(a) (or from_numpy(a).clone())."))

add('contiguous-layout', 'Tensor.contiguous: copies only when the layout requires it',
    GEN+'torch.Tensor.contiguous.html#torch.Tensor.contiguous', [
    "A tensor is contiguous when its elements are laid out in row-major order without gaps. Transposes and some slices are views with other strides and are not contiguous; view() and some kernels and exporters require contiguous input.",
    "contiguous() returns the tensor itself when it already is contiguous, and otherwise copies into new row-major memory. Comparing data_ptr() shows whether a copy happened. Axes of length one do not affect contiguity, so a transposed (1, n) tensor is still contiguous.",
    "Each copy costs memory bandwidth. Call contiguous() where it is required, not reflexively everywhere, and measure when performance matters.",
    "The transfer inspects contiguity and copying for a tensor and its transpose."
    ],
    ("When does t.contiguous() return t itself?",
     "When t is already contiguous; otherwise it copies.",
     ["Never; it always copies.", "Only for 1-D tensors.", "Only on GPU."],
     "Check data_ptr() or is_contiguous() rather than assuming a copy."),
    task("Transfer: layout and copying",
         "data is a shape [rows, cols]. With a = arange(rows*cols).reshape(data), t = a.t() and c = t.contiguous(), return [t contiguous, c contiguous, c shares t's memory, a.contiguous() is a, c.view(-1)].",
         "a = torch.arange(data[0] * data[1]).reshape(data)\nt = a.t()\nc = t.contiguous()\nresult = [t.is_contiguous(), c.is_contiguous(), c.data_ptr() == t.data_ptr(), a.contiguous() is a, c.view(-1).tolist()]",
         [([2,3],[False,True,False,True,[0,3,1,4,2,5]]),([1,3],[True,True,True,True,[0,1,2]]),([3,3],[False,True,False,True,[0,3,6,1,4,7,2,5,8]])],
         ("c = t.contiguous()","c = t.clone()"),
         ["A transpose is a strided view.", "contiguous() copies only when needed.", "Length-one axes do not break contiguity."],
         "The 2 × 3 transpose is not contiguous, so contiguous() copies it into new memory, after which view works. The transpose of a single row is already contiguous and is returned as is. clone() keeps the transposed strides, so view would still fail.",
         [[True,True,False,True,[0,3,1,4,2,5]],[False,True,True,True,[0,3,1,4,2,5]],[False,False,False,True,[0,1,2,3,4,5]]],
         TORCH),
    ("Does clone() make a transposed tensor contiguous?", "Not necessarily; it preserves strides. Use contiguous() when row-major layout is required."))

add('safe-weight-load', 'torch.load(weights_only=True) refuses arbitrary objects',
    GEN+'torch.load.html#torch.load', [
    "torch.save uses Python's pickle format, and loading a pickle can execute arbitrary code. torch.load(..., weights_only=True), the default since PyTorch 2.6, restricts unpickling to tensors, primitive types and a small allowlist of containers.",
    "A checkpoint containing other objects, such as datetime values or custom classes, is rejected with an UnpicklingError. Store such metadata as plain strings or numbers, or in a separate JSON file, so checkpoints stay loadable in the safe mode.",
    "map_location='cpu' loads tensors onto the CPU regardless of the device they were saved from. Verify a checkpoint's integrity (for example, a recorded SHA-256 digest) before loading it at all.",
    "The transfer saves a tensor-only checkpoint and one with an extra object, then loads both with weights_only=True."
    ],
    ("A checkpoint contains a datetime.date object. What does torch.load(..., weights_only=True) do?",
     "Refuses it with an UnpicklingError, because the type is not on the allowlist.",
     ["Loads it normally.", "Silently drops the date.", "Converts the date to a string."],
     "Keep checkpoints to tensors and primitive metadata."),
    task("Transfer: weights-only loading",
         "data is a list of weights. Save {'w': tensor} and {'w': tensor, 'when': date(2026, 1, 1)} to buffers and load each with weights_only=True and map_location='cpu'. Return 'loaded' or 'rejected' for each.",
         "def roundtrip(obj):\n    stream = io.BytesIO()\n    torch.save(obj, stream)\n    stream.seek(0)\n    try:\n        torch.load(stream, weights_only=True, map_location='cpu')\n        return 'loaded'\n    except pickle.UnpicklingError:\n        return 'rejected'\nresult = [roundtrip({'w': torch.tensor(data)}), roundtrip({'w': torch.tensor(data), 'when': datetime.date(2026, 1, 1)})]",
         [([1,2],['loaded','rejected']),([0.5],['loaded','rejected']),([3],['loaded','rejected'])],
         ("weights_only=True","weights_only=False"),
         ["weights_only restricts unpickling to an allowlist.", "Tensors and plain containers are allowed.", "Arbitrary Python objects are rejected."],
         "The tensor-only checkpoint loads and the one with a date object is rejected. Disabling weights_only would load both, including whatever code a malicious pickle carried.",
         [['loaded','loaded'],['rejected','rejected'],['rejected','loaded']],
         TORCH+"\nimport datetime, io, pickle"),
    ("Why load checkpoints with weights_only=True?", "Unpickling arbitrary objects can execute code; the safe mode accepts only tensors and plain data."))

add('quantization-error', 'torch.quantize_per_tensor: rounding error and saturation',
    GEN+'torch.quantize_per_tensor.html#torch.quantize_per_tensor', [
    "Quantization stores values as small integers: q = clamp(round(x / scale) + zero_point, qmin, qmax). For qint8, q lies in [-128, 127]. Dequantizing gives (q - zero_point) · scale.",
    "Values inside the representable range have rounding error of at most scale / 2. Values outside it saturate at qmin or qmax, and their error can be huge. Choosing scale is a trade-off: smaller scales are more precise but cover a narrower range.",
    "Calibrate scale and zero point on representative data, and measure the end-to-end accuracy of the quantized model, not just per-tensor error. Outliers, as in the transfer, are the usual cause of poor quantized accuracy.",
    "The transfer quantizes values including an outlier and reports integer codes, reconstructions and the maximum error."
    ],
    ("With scale 0.25 and qint8, what happens to the value 100?",
     "It saturates at code 127, reconstructing as 31.75.",
     ["It is stored exactly as 400.", "It wraps around to a negative code.", "It raises an overflow error."],
     "Out-of-range values clamp to the integer limits."),
    task("Transfer: quantize, dequantize and measure",
         "data is [values, scale]. Quantize with zero_point 0 to qint8 and dequantize. Return [integer codes, reconstructed values, maximum absolute error], rounded to 4 places.",
         "values, scale = data\nx = torch.tensor(values, dtype=torch.float32)\nq = torch.quantize_per_tensor(x, scale=scale, zero_point=0, dtype=torch.qint8)\nback = q.dequantize()\nresult = [q.int_repr().tolist(), [round(v, 4) for v in back.tolist()], round(float((back - x).abs().max()), 4)]",
         [([[1.1,-0.3,100],0.25],[[4,-1,127],[1.0,-0.25,31.75],68.25]),([[0.5,1.0],0.5],[[1,2],[0.5,1.0],0.0]),([[0.1,0.2],0.1],[[1,2],[0.1,0.2],0.0])],
         ("zero_point=0","zero_point=10"),
         ["Codes are round(x / scale) clamped to [-128, 127].", "In-range error is at most scale / 2.", "Outliers saturate and dominate the error."],
         '1.1 / 0.25 rounds to code 4 (1.0, error 0.1) and -0.3 to -1, but 100 needs code 400 and saturates at 127, reconstructing as 31.75 with an error of 68.25. Values on the grid reconstruct exactly. A non-zero zero point shifts every code and changes which values saturate.',
         [[[4,-1,400],[1.0,-0.25,100.0],0.1],[[4,-1,127],[1.1,-0.3,31.75],0.0],[[14,9,127],[1.0,-0.25,29.25],70.75]],
         TORCH),
    ("What bounds quantization error for in-range values?", "Half the scale; out-of-range values saturate with much larger error."))

add('compiled-equivalence', 'torch.compile: check equivalence against eager execution',
    GEN+'torch.compile.html#torch.compile', [
    "torch.compile captures a function or module and runs an optimized version. The goal is identical results with better speed, but capture can change numerics slightly or fail on unsupported Python features.",
    "Treat compilation like any refactor: compare compiled and eager outputs on representative inputs, including edge cases such as zeros and branches, with an appropriate tolerance. backend='eager' exercises the capture machinery without a compiler toolchain, which makes it suitable for a fast correctness check.",
    "Speed claims need measurements on the target hardware after warm-up, because the first call includes compilation time. Record the backend and versions with any result.",
    "The transfer compiles a piecewise function and compares it with eager execution."
    ],
    ("What should you verify before relying on a torch.compile'd function?",
     "That its outputs match eager execution on representative inputs, within tolerance.",
     ["Only that it runs without raising.", "That the first call is faster.", "Nothing; compilation never changes results."],
     "Compilation is a transformation; test equivalence like any refactor."),
    task("Transfer: compiled versus eager",
         "data is a list of numbers. Compile f(x) = where(x > 0, x², -x) + 1 with backend='eager'. Return [compiled outputs, whether compiled and eager outputs are equal].",
         "def f(x):\n    return torch.where(x > 0, x * x, -x) + 1\ncompiled = torch.compile(f, backend='eager')\ninputs = torch.tensor(data, dtype=torch.float32)\nresult = [compiled(inputs).tolist(), bool(torch.equal(compiled(inputs), f(inputs)))]",
         [([2,-3,0],[[5.0,4.0,1.0],True]),([1],[[2.0],True]),([-0.5,4],[[1.5,17.0],True])],
         ("x * x, -x) + 1","x * x, x) + 1"),
         ["Positive inputs are squared; others are negated.", "Add one to every element.", "Compare with the eager function on the same inputs."],
         "2 maps to 5, -3 to 4 and 0 to 1, and the compiled function matches eager execution. Dropping the negation changes the non-positive branch.",
         [[[5.0,-2.0,1.0],True],[[5.0,4.0,1.0],False],[[4.0,9.0,0.0],True]],
         TORCH),
    ("Why does the first call to a compiled function not measure its speed?", "It includes capture and compilation time; measure after warm-up."))

add('exported-program', 'torch.export: static shapes versus a dynamic batch dimension',
    DOCS+'export.html#expressing-dynamism', [
    "torch.export captures a model as a graph with explicit input constraints. By default, input shapes are specialized to the example: an export traced with batch size 2 rejects a batch of 3.",
    "Declaring a dimension dynamic, dynamic_shapes={'x': {0: torch.export.Dim('batch')}}, makes the graph accept any batch size the model's operations allow. The constraint is recorded in the exported program, which documents its contract.",
    "Deployment code should test the exported program with the shapes it will actually see, including batch sizes other than the example. Exported graphs also fix control flow; data-dependent Python branches need special handling.",
    "The transfer exports a model with static and dynamic batch dimensions and runs both on a different batch size."
    ],
    ("A model is exported with an example batch of 2 and no dynamic_shapes. What happens with a batch of 3?",
     "The exported program rejects it, because the batch dimension was specialized to 2.",
     ["It works; batch dimensions are always dynamic.", "It silently truncates to 2 rows.", "It pads the batch to 4."],
     "Declare dynamic dimensions explicitly with torch.export.Dim."),
    task("Transfer: dynamic batch export",
         "data is a batch of rows of three values. Export Model (row sums × 2) from a (2, 3) example, once with a dynamic batch dimension and once static. Return [dynamic outputs for data, 'accepted' or 'rejected' for the static export].",
         "class Model(torch.nn.Module):\n    def forward(self, x):\n        return x.sum(dim=1, keepdim=True) * 2\nexample = torch.ones(2, 3)\nbatch = torch.export.Dim('batch')\ndynamic = torch.export.export(Model(), (example,), dynamic_shapes={'x': {0: batch}})\nstatic = torch.export.export(Model(), (example,))\nx = torch.tensor(data, dtype=torch.float32)\ntry:\n    static.module()(x)\n    static_result = 'accepted'\nexcept Exception:\n    static_result = 'rejected'\nresult = [dynamic.module()(x).ravel().tolist(), static_result]",
         [([[1,1,1],[2,2,2],[0,0,1]],[[6.0,12.0,2.0],'rejected']),([[1,2,3],[0,0,0]],[[12.0,0.0],'accepted']),([[1,1,1],[1,1,1],[1,1,1],[1,1,1]],[[6.0,6.0,6.0,6.0],'rejected'])],
         ("dynamic_shapes={'x': {0: batch}}","dynamic_shapes=None"),
         ["Exports specialize shapes unless told otherwise.", "Dim marks a dimension as dynamic.", "Test exported programs with production shapes."],
         "The dynamic export handles three rows, while the static one accepts only the example's batch size of two. Removing the dynamic declaration makes the 'dynamic' export reject three rows too.",
         [[[6.0,12.0,2.0],'accepted'],[[3.0,6.0,1.0],'rejected'],[[6.0,12.0],'rejected']],
         TORCH),
    ("How do you let an exported model accept different batch sizes?", "Declare the batch dimension dynamic with torch.export.Dim in dynamic_shapes."))

add('distributed-partition', 'DistributedSampler: padding to equal shards and drop_last',
    GEN.replace('generated/','')+'data.html#torch.utils.data.distributed.DistributedSampler', [
    "In data-parallel training, each process (rank) must see a different part of the dataset every epoch. DistributedSampler assigns indices by striding: rank r takes indices r, r + world, r + 2·world and so on.",
    "Every rank must take the same number of steps, or collective operations deadlock. With drop_last=False the sampler pads by repeating indices from the start so the total divides evenly; with drop_last=True it drops the remainder instead. Either way, some samples are repeated or skipped each epoch, which matters for exact evaluation.",
    "Call sampler.set_epoch(epoch) when shuffling so each epoch uses a different permutation. Passing num_replicas and rank explicitly, as here, lets the partitioning be tested without starting a process group.",
    "The transfer partitions a dataset across ranks with padding and checks coverage."
    ],
    ("Seven samples are split across three ranks with drop_last=False. How many indices does each rank get?",
     "Three; two indices are repeated to pad the total to nine.",
     ["Two, with one sample dropped.", "Seven each.", "2, 2 and 3."],
     "Ranks must take equal numbers of steps, so the sampler pads."),
    task("Transfer: equal shards across ranks",
         "data is [dataset size, world size]. Build DistributedSampler(num_replicas=world, rank=r, shuffle=False) for each rank. Return [index lists per rank, number of padded duplicates, whether every sample is covered].",
         "count, world = data\ndataset = list(range(count))\nshards = [list(DistributedSampler(dataset, num_replicas=world, rank=r, shuffle=False)) for r in range(world)]\nflat = [i for s in shards for i in s]\nresult = [shards, len(flat) - count, sorted(set(flat)) == dataset]",
         [([7,3],[[[0,3,6],[1,4,0],[2,5,1]],2,True]),([4,2],[[[0,2],[1,3]],0,True]),([5,2],[[[0,2,4],[1,3,0]],1,True])],
         ("shuffle=False)","shuffle=False, drop_last=True)"),
         ["Rank r takes every world-th index starting at r.", "Padding repeats indices from the start.", "drop_last drops the remainder instead."],
         "Seven samples over three ranks become nine indices: 0 and 1 are repeated so each rank takes three steps, and every sample is covered. drop_last would give two each and skip one sample.",
         [[[[0,3,6],[1,4],[2,5]],0,True],[[[0,1,2],[3,4,5],[6,0,1]],2,True],[[[0,3],[1,4],[2,5]],-1,False]],
         TORCH+"\nfrom torch.utils.data.distributed import DistributedSampler"),
    ("Why does DistributedSampler pad or drop samples?", "Every rank must take the same number of steps, or collective operations deadlock."))

add('loader-worker-policy', 'DataLoader workers: get_worker_info is None in the main process',
    DOCS+'data.html#multi-process-data-loading', [
    "With num_workers=0, the DataLoader calls the dataset's __getitem__ in the main process. With num_workers > 0, separate worker processes load batches in parallel; each worker has its own copy of the dataset and its own random state.",
    "torch.utils.data.get_worker_info() returns None in the main process and a description (id, num_workers, seed) inside a worker. Datasets use it to split work, such as streaming shards, or to seed per-worker randomness.",
    "Workers add process start-up time, memory and shutdown responsibilities, and on macOS and Windows they are spawned, which requires picklable datasets defined in importable modules. Start with num_workers=0 for correctness, then measure before adding workers.",
    "The transfer records, for each sample, whether it was loaded in the main process."
    ],
    ("What does get_worker_info() return when num_workers=0?",
     "None, because loading happens in the main process.",
     ["A worker id of 0.", "The number of CPU cores.", "It raises an error."],
     "Worker information exists only inside worker processes."),
    task("Transfer: where samples are loaded",
         "data is a dataset size. Each sample records [index, worker id or -1, 1 if loaded in the main process]. Load with batch_size=2 and num_workers=0. Return [rows, loader.num_workers].",
         "class Probe(torch.utils.data.Dataset):\n    def __len__(self):\n        return data\n    def __getitem__(self, i):\n        info = torch.utils.data.get_worker_info()\n        return torch.tensor([i, -1 if info is None else info.id, int(os.getpid() == MAIN)])\nMAIN = os.getpid()\nloader = torch.utils.data.DataLoader(Probe(), batch_size=2, num_workers=0)\nrows = torch.cat(list(loader)).tolist()\nresult = [rows, loader.num_workers]",
         [(3,[[[0,-1,1],[1,-1,1],[2,-1,1]],0]),(1,[[[0,-1,1]],0]),(4,[[[0,-1,1],[1,-1,1],[2,-1,1],[3,-1,1]],0])],
         ("-1 if info is None else info.id","0"),
         ["num_workers=0 loads in the main process.", "get_worker_info() is None outside workers.", "Batches are concatenated back into rows."],
         "Every sample is loaded in the main process with no worker information. Recording a fixed worker id 0 would wrongly suggest a worker loaded them.",
         [[[[0,0,1],[1,0,1],[2,0,1]],0],[[[0,-1,0],[1,-1,0],[2,-1,0]],0],[[[0,-1,1],[1,-1,1],[2,-1,1]],2]],
         TORCH+"\nimport os"),
    ("When should you add DataLoader workers?", "After the single-process pipeline is correct, and only when measurements show loading is the bottleneck."))
