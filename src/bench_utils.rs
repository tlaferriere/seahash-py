#![cfg(feature = "bench")]

use pyo3::{pymodule, PyResult, Python, wrap_pyfunction};
use pyo3::prelude::PyModule;

mod inner {
    use std::fs::File;
    use std::hash::Hasher;
    use std::io::BufWriter;
    use std::io::prelude::*;
    use std::path::PathBuf;

    use pyo3::prelude::*;
    use seahash::SeaHasher;

    #[pyfunction]
    pub(crate) fn prepare_test_data(py: Python, path: PathBuf, size: u64) -> PyResult<(Vec<u8>, u64)> {
        py.allow_threads(|| {
            let f = File::open(path)?;
            let mut w = BufWriter::new(f);
            let mut hasher = SeaHasher::new();
            let mut buf = Vec::with_capacity(size as usize);
            for _ in 0..size {
                let block = hasher.finish();
                let block_bytes = block.to_ne_bytes();
                w.write(&block_bytes)?;
                hasher.write(&block_bytes);
                buf.extend_from_slice(&block_bytes);
            }
            Ok((buf, hasher.finish()))
        })
    }
}
#[pymodule]
pub(crate) fn bench_utils(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(inner::prepare_test_data, m)?)?;
    Ok(())
}
