(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const out = {};
  try {
    for (let i = 0; i < 40 && !window.__AF; i++) await sleep(250);
    if (!window.__AF) return { error: 'no __AF handle' };
    const AF = window.__AF;
    out.babylon = BABYLON.Version;
    out.skeletonBones = AF.skeleton ? AF.skeleton.bones.map(b => b.name) : null;
    out.meshCount = AF.meshes.length;
    out.meshesSkinned = AF.meshes.filter(m => m.skeleton === AF.skeleton).length;
    out.influencers = [...new Set(AF.meshes.map(m => m.numBoneInfluencers))];
    out.polyCounter = document.getElementById('poly-counter').textContent;

    const bones = AF.skeleton.bones;
    const idxOf = n => AF.BONE_HIERARCHY.findIndex(b => b.name === n);
    function lbs(mesh, vIdx) {
      const pos = mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
      const mi = mesh.metadata.matricesIndices, mw = mesh.metadata.matricesWeights;
      const v = new BABYLON.Vector3(pos[vIdx * 3], pos[vIdx * 3 + 1], pos[vIdx * 3 + 2]);
      let acc = new BABYLON.Vector3(0, 0, 0);
      for (let k = 0; k < 4; k++) {
        const w = mw[vIdx * 4 + k]; if (!w) continue;
        const bone = bones[mi[vIdx * 4 + k]];
        const m = bone.getInvertedAbsoluteTransform().multiply(bone.getWorldMatrix());
        acc.addInPlace(BABYLON.Vector3.TransformCoordinates(v, m).scale(w));
      }
      return { v, acc };
    }

    // --- Test 1: bind pose identity (animMode bind = T-Pose button setting) ---
    AF.state.animMode = 'bind';
    Object.keys(AF.state.manualBoneOffsets).forEach(k => AF.state.manualBoneOffsets[k] = { rx: 0, ry: 0, rz: 0 });
    await sleep(700);
    let maxDev = 0, sampled = 0;
    AF.meshes.forEach(mesh => {
      const pos = mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
      const nv = pos.length / 3;
      for (let vi = 0; vi < nv; vi += 37) {
        const { v, acc } = lbs(mesh, vi);
        maxDev = Math.max(maxDev, BABYLON.Vector3.Distance(v, acc));
        sampled++;
      }
    });
    out.bindPose = { sampledVerts: sampled, maxDeviation: +maxDev.toFixed(5) };

    // --- Test 2: elbow bend blends (not rigid, not static) ---
    AF.state.manualBoneOffsets['Elbow_L'] = { rx: 90, ry: 0, rz: 0 };
    await sleep(700);
    let blendEvidence = null, maxMove = 0;
    for (const mesh of AF.meshes) {
      const pos = mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
      const mi = mesh.metadata.matricesIndices, mw = mesh.metadata.matricesWeights;
      const nv = pos.length / 3;
      for (let vi = 0; vi < nv; vi++) {
        const { v, acc } = lbs(mesh, vi);
        const moved = BABYLON.Vector3.Distance(v, acc);
        if (moved > maxMove) maxMove = moved;
        if (!blendEvidence) {
          // vertex split across Elbow_L and another bone
          let wElbow = 0, others = [];
          for (let k = 0; k < 4; k++) {
            if (mi[vi * 4 + k] === idxOf('Elbow_L')) wElbow = mw[vi * 4 + k];
            else if (mw[vi * 4 + k] > 0.25) others.push(mi[vi * 4 + k]);
          }
          if (wElbow > 0.25 && wElbow < 0.8 && others.length) {
            // rigid-follow-elbow comparison
            const bE = bones[idxOf('Elbow_L')];
            const mE = bE.getInvertedAbsoluteTransform().multiply(bE.getWorldMatrix());
            const rigid = BABYLON.Vector3.TransformCoordinates(v, mE);
            const dRigid = BABYLON.Vector3.Distance(acc, rigid);
            const dBind = BABYLON.Vector3.Distance(acc, v);
            if (dRigid > 0.005 && dBind > 0.005) {
              blendEvidence = { mesh: mesh.name, wElbow: +wElbow.toFixed(2), distFromBind: +dBind.toFixed(3), distFromRigidElbow: +dRigid.toFixed(3) };
            }
          }
        }
      }
      if (blendEvidence && maxMove > 0.3) break;
    }
    out.elbowBend = { maxVertexMove: +maxMove.toFixed(3), blendEvidence };
    AF.state.manualBoneOffsets['Elbow_L'] = { rx: 0, ry: 0, rz: 0 };
    AF.state.animMode = 'idle';
    await sleep(300);

    // --- Test 3: real Export button -> validation report ---
    document.getElementById('btn-export-glb').click();
    for (let i = 0; i < 40 && !window.__lastExportReport; i++) await sleep(250);
    out.exportReport = window.__lastExportReport || null;
    out.statusText = document.getElementById('status-text').textContent;

    // --- Test 4: re-import the exported GLB into a fresh scene ---
    const engine = AF.scene.getEngine();
    const scene2 = new BABYLON.Scene(engine);
    const glb = await BABYLON.GLTF2Export.GLBAsync(AF.scene, 'anthroforge_avatar', {
      shouldExportNode: n => !n.name.startsWith('joint_') && !n.name.startsWith('dropRing_') && !['pedestal', 'pedestalRing', 'innerRing'].includes(n.name)
    });
    const files = glb.glTFFiles; const key = Object.keys(files).find(k => k.endsWith('.glb'));
    const url = URL.createObjectURL(files[key]);
    const res = await BABYLON.SceneLoader.ImportMeshAsync('', '', url, scene2, null, '.glb');
    const skinned = res.meshes.filter(m => m.skeleton);
    out.reimport = {
      meshes: res.meshes.length,
      skinnedMeshes: skinned.length,
      skeletons: scene2.skeletons.map(s => s.bones.length),
      sampleSkinnedNames: skinned.slice(0, 5).map(m => m.name)
    };
    URL.revokeObjectURL(url);
  } catch (e) { out.error = String(e && e.stack || e); }
  return out;
})()