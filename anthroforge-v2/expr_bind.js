(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const AF = window.__AF;
  AF.state.animMode = 'bind';
  AF.state.drivers = { jawOpen: 0, earPerk: 50, wingSpread: 50, tailCurl: 50 };
  AF.state.sos.lift = 0; AF.state.sos.curve = 0;
  Object.keys(AF.state.manualBoneOffsets).forEach(k => AF.state.manualBoneOffsets[k] = { rx: 0, ry: 0, rz: 0 });
  await sleep(800);
  const bones = AF.skeleton.bones;
  let maxDev = 0, worst = null, sampled = 0;
  AF.meshes.forEach(mesh => {
    const pos = mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
    const mi = mesh.metadata.matricesIndices, mw = mesh.metadata.matricesWeights;
    const nv = pos.length / 3;
    for (let vi = 0; vi < nv; vi += 7) {
      const v = new BABYLON.Vector3(pos[vi * 3], pos[vi * 3 + 1], pos[vi * 3 + 2]);
      let acc = new BABYLON.Vector3(0, 0, 0);
      for (let k = 0; k < 4; k++) {
        const w = mw[vi * 4 + k]; if (!w) continue;
        const b = bones[mi[vi * 4 + k]];
        const m = b.getInvertedAbsoluteTransform().multiply(b.getWorldMatrix());
        acc.addInPlace(BABYLON.Vector3.TransformCoordinates(v, m).scale(w));
      }
      const d = BABYLON.Vector3.Distance(v, acc);
      if (d > maxDev) { maxDev = d; worst = mesh.name; }
      sampled++;
    }
  });
  return { sampledVerts: sampled, maxDeviation: +maxDev.toFixed(6), worstMesh: worst };
})()