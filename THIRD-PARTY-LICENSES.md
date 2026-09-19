# Third-Party Notices

This file collects the license notices that Foq is required to retain for the
third-party components it builds upon. The list is kept short and factual.

## Reference model weights (Apache License 2.0)

The reference GGUF weights used by the Foq engine (`foq-reflex-8b`,
`foq-juge-27b`) are ternary-quantized builds derived from open-weight model
families distributed under the Apache License 2.0.

Copyright and attribution notices for those families are retained in the
`general.license` metadata of each GGUF file, as required by Apache 2.0 §4.
Copies of the Apache License 2.0 are available at
<https://www.apache.org/licenses/LICENSE-2.0>.

THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS IN THE
WORK.

## llama.cpp (MIT License)

The inference runtime (`llama-server`) is llama.cpp, distributed under the MIT
license — see <https://github.com/ggml-org/llama.cpp>.

## Python dependencies

Runtime dependencies of the `foq` package and their licenses:

| Package | License |
|---|---|
| httpx | BSD 3-Clause |
| numpy | BSD 3-Clause |
| fastapi (optional, `security`) | MIT |
| uvicorn (optional, `security`) | BSD 3-Clause |
| playwright (optional, `browser`) | Apache 2.0 |
| scipy (optional, `calibration`) | BSD 3-Clause |
| pydantic (optional, `extract`) | MIT |
