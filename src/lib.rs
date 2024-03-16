use pyo3::prelude::*;

mod inner {
    use std::any::Any;
    use std::hash::Hasher;

    #[cfg(Py_3_11)]
    use pyo3::buffer::PyBuffer;
    use pyo3::exceptions::PyTypeError;
    use pyo3::prelude::*;
    use pyo3::types::{PyBytes, PyType};

    /// Hash some bytes
    #[pyfunction]
    pub(crate) fn hash(py: Python, buf: &[u8]) -> u64 {
        py.allow_threads(|| seahash::hash(buf))
    }

    /// Hash some bytes according to a chosen seed.
    #[pyfunction]
    pub(crate) fn hash_seeded(py: Python, buf: &[u8], a: u64, b: u64, c: u64, d: u64) -> u64 {
        py.allow_threads(|| seahash::hash_seeded(buf, a, b, c, d))
    }

    #[derive(Copy, Clone)]
    #[pyclass]
    pub(crate) struct SeaHash {
        inner: seahash::SeaHasher,
    }

    #[pymethods]
    impl SeaHash {
        #[pyo3(name = "digest_size")]
        #[classattr]
        const DIGEST_SIZE: u8 = 8;

        #[pyo3(name = "block_size")]
        #[classattr]
        const BLOCK_SIZE: u8 = 8;

        #[new]
        #[pyo3(signature = (data = Vec::new()))]
        fn new(data: Vec<u8>) -> Self {
            let mut inner = seahash::SeaHasher::new();
            inner.write(data.as_slice());
            SeaHash { inner }
        }

        #[cfg(not(Py_3_11))]
        pub fn update(&mut self, py: Python, obj: &[u8]) {
            py.allow_threads(|| self.inner.write(obj))
        }

        #[cfg(Py_3_11)]
        pub fn update(&mut self, py: Python, obj: &PyAny) -> PyResult<()> {
            if let Ok(buf) = obj.extract() {
                py.allow_threads(|| self.inner.write(buf));
                return Ok(());
            };
            if obj.get_type().name()? != "memoryview" {
                return Err(PyTypeError::new_err("Expected a bytes-like object."));
            };
            let py_buffer: PyBuffer<u8> = PyBuffer::get(obj)?;
            let buf_ptr = py_buffer.buf_ptr() as *const u8;
            let len = py_buffer.len_bytes();
            let slice = unsafe { std::slice::from_raw_parts(buf_ptr, len) };
            // We cannot unlock the GIL here since we are unsafely accessing the buffer of the memoryview owned by Python
            self.inner.write(slice);
            Ok(())
        }

        pub fn digest(&self, py: Python) -> PyObject {
            PyBytes::new(py, &self.intdigest().to_ne_bytes()).into()
        }

        pub fn intdigest(&self) -> u64 {
            self.inner.finish()
        }

        pub fn hexdigest(&self) -> String {
            format!("{:x}", self.intdigest())
        }

        pub fn copy(&self) -> Self {
            // Self derives Copy
            *self
        }
    }
}
/// A Python module implemented in Rust.
#[pymodule]
fn seahash(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_function(wrap_pyfunction!(inner::hash, m)?)?;
    m.add_function(wrap_pyfunction!(inner::hash_seeded, m)?)?;
    m.add_class::<inner::SeaHash>()?;
    Ok(())
}
