/*jshint esversion: 6 */
// @ts-check

/**
 * Graphics Town Framework - "Main" File
 *
 * This is the main file - it creates the world, populates it with
 * objects and behaviors, and starts things running
 *
 * The initial distributed version has a pretty empty world.
 * There are a few simple objects thrown in as examples.
 *
 * It is the students job to extend this by defining new object types
 * (in other files), then loading those files as modules, and using this
 * file to instantiate those objects in the world.
 */

import { GrWorld } from "../libs/CS559-Framework/GrWorld.js";
import { WorldUI } from "../libs/CS559-Framework/WorldUI.js";
import * as T from "../libs/CS559-Three/build/three.module.js";
import { shaderMaterial } from "../libs/CS559-Framework/shaderHelper.js";
import {main} from "../examples/main.js";
import { GrGroup, GrSquareSign } from "../libs/CS559-Framework/SimpleObjects.js";
import { GrObject } from "../libs/CS559-Framework/GrObject.js";
import { DoubleSide, MeshStandardMaterial, Object3D, Vector3 } from "../libs/CS559-Three/build/three.module.js";
import { GLTFLoader } from "../libs/CS559-Three/examples/jsm/loaders/GLTFLoader.js";

// Make my own ground plane to look sandy
let groundCtr = 0;
class groundGR extends GrObject{
    /**
     * This is a ground object that I made so that I could use the sand texture on it
     * 
     * @param {Object} [params]
     * @param {THREE.Material} [params.material]
     * @param {number} [params.x]
     * @param {number} [params.y]
     * @param {number} [params.z]
     * @param {number} [params.size]
     */
     constructor(params = {}, paramInfo = []) {
        let material = shaderMaterial("../for_students/final-grtown-sand.vs",
            "../for_students/final-grtown-sand.fs", {
            side: T.DoubleSide,
            uniforms: {},
        });
        const size = params.size ?? 0.5;
        const geometry = new T.BoxBufferGeometry(size,0.25,size);
        
    
        // note that we have to make the Object3D before we can call
        // super and we have to call super before we can use this
        const mesh = new T.Mesh(geometry, material);
        super(`Ground-${groundCtr++}`, mesh, paramInfo);
    
        // put the object in its place

        mesh.rotateY(Math.PI/2);

        mesh.position.x = Number(params.x) || 0 ;
        mesh.position.y = Number(params.y) || 0 - 0.25;
        mesh.position.z = Number(params.z) || 0 ;

        this.mesh = mesh;
      }
}

// Palm Tree
let treeCtr = 0;
class palmtreeGR extends GrObject{
    /**
     * A simple palm tree
     * 
     * @param {Object} [params]
     * @param {THREE.Material} [params.material]
     * @param {number} [params.x]
     * @param {number} [params.y]
     * @param {number} [params.z]
     * @param {number} [params.size]
     */
     constructor(params = {}, paramInfo = []) {
        let trunkMat = shaderMaterial("../for_students/final-grtown-sand.vs",
        "../for_students/final-grtown-wood.fs", {
        side: T.DoubleSide,
        uniforms: {},
        });
        const size = params.size ?? 1.0;
        const trunkGeo = new T.CylinderBufferGeometry(0.075,0.25,4);
        
        const trunk = new T.Mesh(trunkGeo, trunkMat);
        trunk.translateY(4);
        

        // make a leaf
        let exSettings = {
            steps: 2,
            depth: 0.05,
            bevelEnabled: true,
            bevelThickness:0.025,
            bevelSize:0.02
        };

        let leafCurve = new T.Shape();
        leafCurve.quadraticCurveTo(1,0,1,1);
        leafCurve.quadraticCurveTo(0,1,0,0);
        leafCurve.closePath();

        let leafGeo = new T.ExtrudeGeometry(leafCurve, exSettings);
        let leafMat = new T.MeshStandardMaterial({
            color:"green",
            roughness:1,
            flatShading:true,
        });

        let leaf1 = new T.Mesh(leafGeo,leafMat);
        leaf1.translateY(2);
        leaf1.rotateX(Math.PI/2);

        // make leaf copies, rotate appropriately
        let leaf2 = leaf1.clone();
        leaf2.rotateZ(Math.PI/2);

        let leaf3 = leaf1.clone();
        leaf3.rotateZ(Math.PI);

        let leaf4 = leaf1.clone();
        leaf4.rotateZ(-Math.PI/2);

        // angle all leaves down
        leaf1.rotateX(0.25);
        leaf1.rotateY(-0.25);

        leaf2.rotateX(0.25);
        leaf2.rotateY(-0.25);   
        
        leaf3.rotateX(0.25);
        leaf3.rotateY(-0.25);

        leaf4.rotateX(0.25);
        leaf4.rotateY(-0.25);
        
        trunk.add(leaf1);
        trunk.add(leaf2);
        trunk.add(leaf3);
        trunk.add(leaf4);

        // make some coconuts
        let cocoGeo = new T.SphereBufferGeometry(0.125);
        let cocoMat = new T.MeshStandardMaterial( {color:"#897236"});
        let nut1 = new T.Mesh(cocoGeo,cocoMat);
        let nut2 = new T.Mesh(cocoGeo,cocoMat);
        let nut3 = new T.Mesh(cocoGeo,cocoMat);
        let nut4 = new T.Mesh(cocoGeo,cocoMat);

        nut1.translateX(0.25);
        nut1.translateZ(0.25);
        nut1.translateY(1.75);


        nut2.translateX(-0.25);
        nut2.translateZ(0.25);
        nut2.translateY(1.75);

        nut3.translateX(0.25);
        nut3.translateZ(-0.25);
        nut3.translateY(1.75);

        nut4.translateX(-0.25);
        nut4.translateZ(-0.25);
        nut4.translateY(1.75);

        trunk.add(nut1);
        trunk.add(nut2);
        trunk.add(nut3);
        trunk.add(nut4);

        let nuts = [nut1,nut2,nut3,nut4];

        super(`PalmTree-${treeCtr++}`, trunk, paramInfo);
    
        // put the object in its place

        trunk.scale.set(size,size,size);
        trunk.position.x = Number(params.x) || 0 ;
        trunk.position.y = Number(params.y) || 2*size;
        trunk.position.z = Number(params.z) || 0 ;

        this.mesh = trunk;
        this.nuts = nuts;
        this.tracker = 0;
        this.leafHeight = nut1.position.y;
      }
      stepWorld(delta) {     

        this.nuts[this.tracker].translateY(-0.005*delta);
            
        if(this.nuts[this.tracker].position.y<-2){
            this.nuts[this.tracker].position.setY(this.leafHeight);
            this.tracker++;
            if(this.tracker>3) this.tracker = 0;
        }
      }
}

// seagull
let bird = new T.TextureLoader().load("../for_students/images/bird.jpg");
let gullCtr = 0;
class seagullGR extends GrObject{
    /**
     *  A seagull with wings that flap as it moves about
     * 
     * @param {Object} [params]
     * @param {THREE.Material} [params.material]
     * @param {number} [params.x]
     * @param {number} [params.y]
     * @param {number} [params.z]
     * @param {number} [params.size]
     * @param {array}  [params.destination]
     * @param {number} [params.speed] 
     */
     constructor(params = {}, paramInfo = []) {
        const size = params.size ?? 1.0;

        let bird_geo = new T.BufferGeometry();
    
        const bird_verticies = new Float32Array( [ 
            // beak
            -0.25,0,0,
            0.25,0,-0.5,
            -0.25,0,-0.5,
            -0.25,0,0,
            0.25,0,-0.5,
            0.25,0,0,

            //body
            // top front
            -0.25,0,-0.5,
            0.25,0.5,-1.5,
            -0.25,0.5,-1.5,
            -0.25,0,-0.5,
            0.25,0.5,-1.5,
            0.25,0,-0.5,

            // top rear
            -0.25,0.5,-1.5,
            0.25,0,-4,
            -0.25,0,-4,
            -0.25,0.5,-1.5,
            0.25,0,-4,
            0.25,0.5,-1.5,

            // right side
            0.25,0,-0.5,
            0.25,0.5,-1.5,
            0.25,0,-1.5,
            0.25,0.5,-1.5,
            0.25,0,-1.5,
            0.25,0,-4,

            // left side
            -0.25,0,-0.5,
            -0.25,0.5,-1.5,
            -0.25,0,-1.5,
            -0.25,0.5,-1.5,
            -0.25,0,-1.5,
            -0.25,0,-4,

            // belly
            -0.25,0,-0.5,
            0.25,0,-4,
            -0.25,0,-4,
            -0.25,0,-0.5,
            0.25,0,-4,
            0.25,0,-0.5,

        ]);
    
        bird_geo.setAttribute('position', new T.BufferAttribute(bird_verticies,3));
        bird_geo.computeVertexNormals();
    
        const bird_uvs = new Float32Array([
            // beak
            138/695,356/700,
            130/695,359/700,
            138/695,359/700,
            138/695,356/700,
            130/695,359/700,
            138/695,359/700,

            // body front
            0.75,0,
            1,0.25,
            1,0,
            0.75,0,
            1,0.25,
            0.75,0.25,

            // body rear
            0.75,0,
            1,0.25,
            1,0,
            0.75,0,
            1,0.25,
            0.75,0.25,

            // right side
            0.6,0,
            0.75,0.25,
            0.75,0,
            0.75,0.25,
            0.75,0,
            1,0,

            // left side
            0.6,0,
            0.75,0.25,
            0.75,0,
            0.75,0.25,
            0.75,0,
            1,0,

            // belly
            0.5,0,
            0.6,0.25,
            0.6,0,
            0.5,0,
            0.6,0.25,
            0.5,0.25,
        ]);
      
        
        bird_geo.setAttribute('uv',new T.BufferAttribute(bird_uvs,2));
    
        let bird_mat = new T.MeshStandardMaterial({
            color: "white",
            roughness: 0,
            side: DoubleSide,
            map: bird,
            metalness:0
          });

        
        let seagull = new T.Mesh(bird_geo,bird_mat);

        // create wings
        let lwing_geo = new T.BufferGeometry();
    
        const lwing_verticies = new Float32Array( [ 
            // forearm
            -0.25,0.125,-1.5,
            -0.25,0.125,-2.25,
            -2,0.125,-1.5,

            // wingtips
            -2,0.125,-1.5,
            -2.5,0.125,-2.75,
            -1.25,0.125,-1.5
        ] );

        lwing_geo.setAttribute('position', new T.BufferAttribute(lwing_verticies,3));
        lwing_geo.computeVertexNormals();

        const lwing_uvs = new Float32Array([
            0.75,0,
            1,0.25,
            1,0,
            0.5,0,
            0.6,0.25,
            0.5,0.25,

        ]);

        lwing_geo.setAttribute('uv', new T.BufferAttribute(lwing_uvs,2));


        let lwing = new T.Mesh(lwing_geo,bird_mat);

        let rwing_geo = new T.BufferGeometry();
    
        const rwing_verticies = new Float32Array( [ 
            // forearm
            0.25,0.125,-1.5,
            0.25,0.125,-2.25,
            2,0.125,-1.5,

            // wingtips
            2,0.125,-1.5,
            2.5,0.125,-2.75,
            1.25,0.125,-1.5
        ] );
        rwing_geo.setAttribute('position', new T.BufferAttribute(rwing_verticies,3));
        rwing_geo.computeVertexNormals();
        rwing_geo.setAttribute('uv', new T.BufferAttribute(lwing_uvs,2));

        let rwing = new T.Mesh(rwing_geo,bird_mat);

        seagull.add(rwing);
        seagull.add(lwing);

        let ride = new Object3D();
        seagull.add(ride);

        let tarGeo = new T.SphereGeometry();
        let tarmat = new MeshStandardMaterial({visible:true, color:"white"});
        let target = new T.Mesh(tarGeo,tarmat);
        target.translateY(Number(params.y) || 6);

        let circle = true;
        let start = 0;

        super(`Seagull-${gullCtr++}`, seagull, paramInfo);
        this.rideable = ride;

        // Are we using default circling behavior or are we going to a bunch of destinations?
        if(typeof params.destination !== 'undefined') {
            circle = false;
            start = Math.floor(Math.random()*params.destination.length);
        }

        // put the object in its place

        seagull.scale.set(size,size,size);
        seagull.position.x = Number(params.x) || 0 ;
        seagull.position.y = Number(params.y) || 6;
        seagull.position.z = Number(params.z) || 0 ;

        // flapping components
        this.lwing = lwing;
        this.rwing = rwing;
        this.progress = 0;
        this.up = true;

        // circular components
        this.seagull = seagull;
        this.target = target;      
        this.running = 0;
        this.circle = circle;

        // destination components
        this.dx = 0;                            // destination coordinates
        this.dy = 0;
        this.dz = 0;
        this.start = start;                     // int for choosing correct desinatoin
        this.destination = params.destination;  // all destinations
        this.new = true;                        // when to switch
        this.speed = Number(params.speed) || 0.005;                      // speed adjustment
        // this.tt = 0;
      }
      stepWorld(delta) {
          // flap wings
            if(this.up){     
                this.lwing.setRotationFromAxisAngle(new T.Vector3(0,0,1), 0.001*delta*this.progress);
                this.rwing.setRotationFromAxisAngle(new T.Vector3(0,0,-1), 0.001*delta*this.progress);
                this.progress++;
                if(this.progress>20) this.up=false;
            } else {
                this.lwing.setRotationFromAxisAngle(new T.Vector3(0,0,1), 0.001*delta*this.progress);
                this.rwing.setRotationFromAxisAngle(new T.Vector3(0,0,-1), 0.001*delta*this.progress);
                this.progress--;
                if(this.progress<-20) this.up=true;
            }

        // Default flight style: circling
        if(this.circle) {
            this.running+=delta/1000;
            let x = 4 * Math.cos(this.running);
            let z = 4 * Math.sin(this.running);
            this.seagull.position.x = x;
            this.seagull.position.z = z;    

            let x2 = 4 * Math.cos(this.running+0.001);
            let z2 = 4 * Math.sin(this.running+0.001);
            this.target.position.x = x2;
            this.target.position.z = z2;
            
            this.seagull.lookAt(this.target.position);
        }
        else { // we are now cycling between destinations
            if(this.new){ // if we have just received a new target      
                // get new destination
                // old behavior, start from a random, move along preset
                //this.start++;
                //if(this.start>=this.destination.length) this.start = 0;
                
                // new: start from random, move to random
                let t = Math.floor(Math.random()*this.destination.length);
                // ensure new destination
                while(this.start == t){
                    t = Math.floor(Math.random()*this.destination.length);
                }
                this.start = t;
                
                this.dx = this.destination[this.start].x;
                this.dy = this.destination[this.start].y;
                this.dz = this.destination[this.start].z;

                // adjust seagull
                this.seagull.lookAt(new T.Vector3(this.dx,this.dy,this.dz));
                this.new = false;
            }

            // move the gull
            this.seagull.translateOnAxis(new Vector3(0,0,1), this.speed*delta);

            // check to see if we have arrived
            if(Math.abs(this.dx - this.seagull.position.x) < 0.1 &&
                Math.abs(this.dy - this.seagull.position.y) < 0.1 &&
                Math.abs(this.dz - this.seagull.position.z) < 0.1) {
                    // we have arrived, move on to next target
                    this.new = true;
            }

        }
        
      }
}

// snowman
let snowManDuoCtr = 0;
class snowmanDuoGR extends GrObject{
    /**
     * This is a pair of dancing snowman
     * 
     * @param {Object} [params]
     * @param {THREE.Material} [params.material]
     * @param {number} [params.x]
     * @param {number} [params.y]
     * @param {number} [params.z]
     * @param {number} [params.scale]
     * @param {boolean} [params.counter]
     */
     constructor(params = {}, paramInfo = []) {
        // bottom
    let sphere = new T.SphereGeometry(1,32,64);
    let snow = new T.MeshPhongMaterial();
    snow.color.set("#f7f7f7");

    // torso
    let mid = new T.Mesh(sphere, snow);
    mid.position.y = 2.5;
    mid.scale.divideScalar(4/3);

    let dot = new T.SphereGeometry(0.1,32,16);
    let coal = new T.MeshStandardMaterial();
    coal.roughness = 1;
    coal.color.set("black");

    let lbut = new T.Mesh(dot,coal);
    lbut.position.setY(2.25);
    lbut.position.setZ(0.7);

    let mbut = new T.Mesh(dot,coal);
    mbut.position.setY(2.5);
    mbut.position.setZ(0.75);

    let hbut = lbut.clone();
    hbut.position.setY(2.75);

    let buttons = new T.Group();
    buttons.add(lbut);
    buttons.add(mbut);
    buttons.add(hbut);

    let stick = new T.CylinderGeometry(0.1,0.1,1,16,16);
    let wood = new T.MeshStandardMaterial();
    wood.color.set("brown");

    let wrist = new T.Mesh(stick,wood);
    wrist.position.setY(0.5);

    let f2 = new T.Mesh(stick,wood);
    f2.position.setY(1.1);
    f2.scale.setY(0.3);
    f2.scale.setX(0.5);
    let f1 = f2.clone();
    f1.rotateZ(Math.PI/4);
    f1.position.setX(-0.1);
    let f3 = f2.clone();
    f3.position.setX(0.1);
    f3.rotateZ(-Math.PI/4);

    let arm = new T.Group();
    arm.add(wrist);
    arm.add(f1);
    arm.add(f2);
    arm.add(f3);

    arm.position.setX(0.7);
    arm.position.setY(2.5);

    let arm2 = arm.clone();
    arm2.position.setX(-0.7);
    //arm2.rotateZ(Math.PI/8);

    arm.rotateZ(-Math.PI/1.5);

    // head
    let top = new T.Mesh(sphere, snow);
    top.position.y = 3.5;
    top.scale.divideScalar(2);

    // eyes
    let leye = new T.Mesh(dot,coal);
    leye.position.setX(-0.2);
    leye.position.setZ(0.4);
    leye.position.setY(3.7);
    leye.scale.divideScalar(2);

    let reye = leye.clone();
    reye.position.setX(0.2);
    reye.position.setZ(0.4);
    reye.position.setY(3.7);

    let eyes = new T.Group();
    eyes.add(leye);
    eyes.add(reye);

    // mouth
    let m1 = new T.Mesh(dot,coal);
    m1.position.setX(-0.225);
    m1.position.setY(3.5);
    m1.position.setZ(0.425);
    m1.scale.divideScalar(2);

    let m2 = m1.clone();
    m2.position.setX(-0.125);
    m2.position.setY(3.45);
    m2.position.setZ(0.45);

    let m3 = m1.clone();
    m3.position.setX(0);
    m3.position.setY(3.425);
    m3.position.setZ(0.475);

    let m4 = m2.clone();
    m4.position.setX(0.125);

    let m5 = m1.clone();
    m5.position.setX(0.225);

    let mouth = new T.Group();
    mouth.add(m1);
    mouth.add(m2);
    mouth.add(m3);
    mouth.add(m4);
    mouth.add(m5);

    // nose
    let cone = new T.ConeGeometry(0.1,0.4,32);
    let veg = new T.MeshStandardMaterial();
    veg.color.set("orange");
    let carrot = new T.Mesh(cone,veg);
    carrot.position.setY(3.6);
    carrot.position.setZ(0.6);
    carrot.rotateX(Math.PI/2);
    
    // rim
    let disk = new T.TorusGeometry(0.3,0.05,16,32);
    let felt = new T.MeshStandardMaterial();
    felt.color.set("#3e3f40");
    felt.roughness = 0.1;

    let rim = new T.Mesh(disk,felt);
    rim.position.setY(4);
    rim.rotateX(Math.PI/2);

    // hat
    let cyl = new T.CylinderGeometry(0.26,0.25,0.75,16,16);
    let dome = new T.Mesh(cyl, felt);
    dome.position.setY(4);

    let hat = new T.Group();
    hat.add(rim);
    hat.add(dome);

    let head = new T.Group();
    head.add(top);
    head.add(eyes);
    head.add(mouth);
    head.add(carrot);
    head.add(hat);

    let torso = new T.Group();
    torso.add(mid);
    torso.add(buttons);

    let bot = new T.Mesh(sphere, snow);
    bot.position.y = 1;

    let snowman = new T.Group();
    snowman.add(head);
    snowman.add(torso);
    snowman.add(bot);
    snowman.add(arm);
    snowman.add(arm2);

    let head2 = head.clone();
    let arm3 = arm.clone();
    let arm4 = arm2.clone();
    let bot2 = bot.clone();
    let torso2 = torso.clone();

    let snowman2 = new T.Group();
    snowman2.add(head2,arm3,arm4,bot2,torso2);
    snowman2.rotateY(Math.PI);
    snowman2.translateX(-3);
    snowman.add(snowman2);


    snowman.position.setX(-1.8);
    super(`SnowmanDuo-${snowManDuoCtr++}`, snowman, paramInfo);

    // put the object in its place

    snowman.rotateY(Math.PI/2);

    snowman.position.x = Number(params.x) || 0 ;
    snowman.position.y = Number(params.y) || 0 ;
    snowman.position.z = Number(params.z) || 0 ;

    const size = params.scale ?? 1.0;
    snowman.scale.set(size,size,size);
    const spin = params.counter ?? true;

    this.head = head;
    this.head2 = head2;

    this.arm2 = arm2;
    this.arm4 = arm4;
    this.snowman = snowman;
    this.snowman2 = snowman2;
    this.counter = spin;

    this.mesh = snowman;

    }
    stepWorld(delta){
        // We get our direction that the arm should be rotating by
            // examining the outer snowmans position relative to the inner
        let temp = new T.Vector3(0,0,0);
        this.snowman2.getWorldPosition(temp);

        if(this.counter) {
            // spin the whole thing
            this.snowman.rotateY(0.001*delta);      
      
            // articulate the arm and head
            if(temp.x - this.snowman.position.x < 0){ 
                this.arm4.rotateZ(delta*0.001);
                this.arm2.rotateZ(delta*0.001);
                this.head.rotateY(delta*0.0005);
                this.head2.rotateY(delta*0.0005);
            }
            else {
                this.arm4.rotateZ(-delta*0.001);
                this.arm2.rotateZ(-delta*0.001);
                this.head.rotateY(-delta*0.0005);
                this.head2.rotateY(-delta*0.0005);
            }
        }
        else { 
            // spin the whole thing
            this.snowman.rotateY(-0.001*delta);

            // articulate the arm and head
            if(temp.x - this.snowman.position.x < 0){ 
                
                this.arm4.rotateZ(-delta*0.001);
                this.arm2.rotateZ(-delta*0.001);
                this.head.rotateY(-delta*0.0005);
                this.head2.rotateY(-delta*0.0005);
            }
            else {
                this.arm4.rotateZ(delta*0.001);
                this.arm2.rotateZ(delta*0.001);
                this.head.rotateY(delta*0.0005);
                this.head2.rotateY(delta*0.0005);
            }
        }
        
    }
}


// beach house
let building = new T.TextureLoader().load("../for_students/images/house.png");
let wood = new T.TextureLoader().load("../for_students/images/wood.jpg");
let beachHouseCtr = 0;
/**
 * @typedef b2Param
 * @type {object}
 * @property {number} [x=0]
 * @property {number} [y=0]
 * @property {number} [z=0]
 * @property {number} [rotate=0]
 * @property {number} [scale=1]
 */
 export class beachHouseGR extends GrObject {
    /**
     * @param {b2Param} params
     */ 
        constructor(params = {}, paramInfo = []) {
          
        let house_geometry = new T.BufferGeometry();
    
        const house_verticies = new Float32Array( [ 
            // bottom
            -0.5,0,-1,
            0.5,0,-1,
            0.5,0,1,         

            -0.5,0,-1,
            0.5,0,1,
            -0.5,0,1,

            // right side
            0.5,0,-1,
            0.5,0.5,1,
            0.5,0,1,

            0.5,0,-1,
            0.5,0.5,-1,
            0.5,0.5,1,

            // left side
            -0.5,0,1,
            -0.5,0.5,-1,
            -0.5,0,-1,

            -0.5,0,1,
            -0.5,0.5,1,
            -0.5,0.5,-1,

            // front
            -0.5,0,1,     
            0.5,0,1,
            0.5,0.5,1,

            -0.5,0,1,    
            0.5,0.5,1,
            -0.5,0.5,1,

            0.5,0.5,1,
            0,1,1,            
            -0.5,0.5,1,

            // back
            0.5,0,-1,
            -0.5,0,-1,
            -0.5,0.5,-1,
            
            0.5,0,-1, 
            -0.5,0.5,-1,
            0.5,0.5,-1,

            -0.5,0.5,-1,
            0,1,-1,            
            0.5,0.5,-1,
      
        ]);
    
        house_geometry.setAttribute('position', new T.BufferAttribute(house_verticies,3));
        house_geometry.computeVertexNormals();
    
        const house_uvs = new Float32Array([
            // botttom
            0,0,
            0.1,0.1,
            0.1,0,
            0,0,
            0.1,0.1,
            0.1,0,

            // right
            0.05,0.3,
            0.4,1,
            0.4,0.3,
            0.05,0.3,
            0.05,1,
            0.4,1,

            // left
            0.05,0.3,
            0.4,1,
            0.4,0.3,
            0.05,0.3,
            0.05,1,
            0.4,1,

            // front
            0.25,0,      
            0.75,0,
            0.75,1,
            0.25,0,           
            0.75,1,
            0.25,1,

            0.1,0.5,
            0.125,0.55,
            0.15,0.5,
            // back
            0.25,0,      
            0.75,0,
            0.75,1,
            0.25,0,           
            0.75,1,
            0.25,1,

            0.1,0.5,
            0.125,0.55,
            0.15,0.5,
            
        ]);
      
        
        house_geometry.setAttribute('uv',new T.BufferAttribute(house_uvs,2));
    
        let house_material = new T.MeshStandardMaterial({
            color: "white",
            roughness: 0.75,
            map: building
          });

        
        let house_mesh = new T.Mesh(house_geometry,house_material);

        let roof_geometry = new T.BufferGeometry();

        let roof_verticies = new Float32Array([
            // roof right
            0.5,0.5,-1,          
            0,1,-1,
            0.5,0.5,1,
            
            
            0.5,0.5,1, 
            0,1,-1,
            0,1,1,
            

            // roof left
            -0.5,0.5,1,         
            0,1,-1,
            -0.5,0.5,-1,

            -0.5,0.5,1,          
            0,1,1,
            0,1,-1,
        ]);

        roof_geometry.setAttribute('position', new T.BufferAttribute(roof_verticies,3));
        roof_geometry.computeVertexNormals();

        const roof_uvs = new Float32Array([
            0,0,
            0,1,
            1,0,
            1,0,
            0,1,
            1,1,
            0,0,
            0,1,
            1,0,
            1,0,
            0,1,
            1,1,
        ]);

        roof_geometry.setAttribute('uv',new T.BufferAttribute(roof_uvs,2));

        let roof_material = new T.MeshStandardMaterial({
            color: "white",
            roughness: 0.75,
            map: wood
        });
        
        let roof = new T.Mesh(roof_geometry,roof_material);
        house_mesh.add(roof);
    
        //super("BeachHouse", house_mesh);
        super(`BeachHouse-${beachHouseCtr++}`, house_mesh, paramInfo);

        // put the object in its place
        house_mesh.position.x = params.x ? Number(params.x) : 0;
        house_mesh.position.y = params.y ? Number(params.y) : 0;
        house_mesh.position.z = params.z ? Number(params.z) : 0;
        house_mesh.rotateY(params.rotate ? Number(params.rotate) : 0);
        let scale = params.scale ? Number(params.scale) : 1;
        house_mesh.scale.set(scale, scale, scale);

        }
      }

// car that I made in wb 8
let truckCtr = 0;
// rusty found here
// https://ambientcg.com/view?id=PaintedMetal006

let rubber = new T.TextureLoader().load("../for_students/images/rubber.png");
let rust = new T.TextureLoader().load("../for_students/images/rust.png");

/**
 * @typedef truckParam
 * @type {object}
 * @property {number} [x=0]
 * @property {number} [y=0.25]
 * @property {number} [z=0]
 * @property {number} [rotate=0]
 * @property {number} [scale=1]
 * @property {number} [wheel_turn=0]
 */
 export class truckGr extends GrObject {
    /**
     * @param {truckParam} params
     */
        constructor(params = {}, paramInfo = []) {
          
        let body_geometry = new T.BufferGeometry();
        
    
        const body_verticies = new Float32Array( [ 
            // nose
            -0.5,0,0.5,
            0.5,0,0.5,
            0.5,0.25,0.5,

            0.5,0.25,0.5,            
            -0.5,0.25,0.5,
            -0.5,0,0.5,

            // l side
            0.5,0,-1,        
            0.5,0.25,0.5,
            0.5,0,0.5,

            0.5,0,-1,        
            0.5,0.25,-1,
            0.5,0.25,0.5,

            0.5,0.25,-0.5,
            0.5,0.5,-0.5,
            0.5,0.25,0.5,
            
            // r side
            -0.5,0,0.5,        
            -0.5,0.25,0.5,
            -0.5,0,-1,

            -0.5,0.25,0.5,        
            -0.5,0.25,-1,
            -0.5,0,-1,

            -0.5,0.25,0.5,
            -0.5,0.5,-0.5,
            -0.5,0.25,-0.5,

            // rear
            0.5,0,-1,
            -0.5,0,-1,
            -0.5,0.25,-1,

            0.5,0,-1,
            -0.5,0.25,-1,
            0.5,0.25,-1,

            // roof
            -0.5,0.25,0.5,
            0.5,0.25,0.5,
            0.5,0.5,-0.5,

            -0.5,0.25,0.5,
            0.5,0.5,-0.5,
            -0.5,0.5,-0.5,

            0.5,0,-0.5,
            -0.5,0,-0.5,
            -0.5,0.5,-0.5,

            0.5,0,-0.5,
            -0.5,0.5,-0.5,
            0.5,0.5,-0.5,

            // bed
            0.5,0.25,-1,
            -0.5,0.25,-1,
            -0.5,0.25,-0.5,

            -0.5,0.25,-0.5,
            0.5,0.25,-0.5,
            0.5,0.25,-1,

      
        ]);
    
        body_geometry.setAttribute('position', new T.BufferAttribute(body_verticies,3));
        body_geometry.computeVertexNormals();
    
        const house_uvs = new Float32Array([
           0,0,
           1,0,
           1,1,
           1,1,
           0,1,
           0,0,
           0,0,
           1,0,
           1,1,
           1,1,
           0,1,
           0,0,
           0,0,
           1,0,
           1,1,
           1,1,
           0,1,
           0,0,
           0,0,
           1,0,
           1,1,
           1,1,
           0,1,
           0,0,
           0,0,
           1,0,
           1,1,
           1,1,
           0,1,
           0,0,
           0,0,
           1,0,
           1,1,
           1,1,
           0,1,
           0,0,
           0,0,
           1,0,
           1,1,
           1,1,
           0,1,
           0,0,
           0,0,
           1,0,
           1,1,
           1,1,
           0,1,
           0,0,

        ]);
      
        
        body_geometry.setAttribute('uv',new T.BufferAttribute(house_uvs,2));
    
        let body_material = new T.MeshStandardMaterial({
            color: "white",
            roughness: 0,
            map: rust
          });

        
        let body_mesh = new T.Mesh(body_geometry,body_material);
        

        let wheel_geometry = new T.CylinderBufferGeometry(0.1,0.1,0.1);
        
        let tire = new T.MeshStandardMaterial({
            color: "white",
            roughness: 0.75,
            map: rubber
        });

        let wheel1 = new T.Mesh(wheel_geometry,tire);
        wheel1.translateX(0.5);
        wheel1.translateZ(0.25);
        wheel1.translateY(0.05);
        wheel1.rotateZ(Math.PI/2);

        let wheel2 = new T.Mesh(wheel_geometry,tire);
        wheel2.translateX(-0.5);
        wheel2.translateZ(0.25);
        wheel2.translateY(0.05);
        wheel2.rotateZ(Math.PI/2);

        let wheel3 = new T.Mesh(wheel_geometry,tire);
        wheel3.translateX(0.5);
        wheel3.translateZ(-0.6);
        wheel3.translateY(0.05);
        wheel3.rotateZ(Math.PI/2);

        let wheel4 = new T.Mesh(wheel_geometry,tire);
        wheel4.translateX(-0.5);
        wheel4.translateZ(-0.6);
        wheel4.translateY(0.05);
        wheel4.rotateZ(Math.PI/2);
        
        let front_wheels = new T.Group();
        front_wheels.add(wheel1);
        front_wheels.add(wheel2);

        let rear_wheels = new T.Group();
        rear_wheels.add(wheel3);
        rear_wheels.add(wheel4);

        let wheels = new T.Group();
        wheels.add(front_wheels);
        wheels.add(rear_wheels);

        body_mesh.add(wheels);
        
        super(`Truck-${truckCtr++}`, body_mesh, paramInfo);
  
        // put the object in its place
        body_mesh.position.x = params.x ? Number(params.x) : 0;
        body_mesh.position.y = params.y ? Number(params.y) : 0.05;
        body_mesh.position.z = params.z ? Number(params.z) : 0;
        body_mesh.rotateY(params.rotate ? Number(params.rotate) : 0);
        // front_wheels.traverse(wheel => {
        //     wheel.rotateY(params.rotate ? Number(params.rotate) : 0);
        // });
        let scale = params.scale ? Number(params.scale) : 1;
        body_mesh.scale.set(0.75*scale, scale, scale);

        }
      }

// fountain target 

/**
 * @typedef fountainTargetParam
 * @type {object}
 * @property {number} [x=0]
 * @property {number} [y=0]
 * @property {number} [z=0]

 */
 export class fountainTargetGR extends GrObject {
    /**
     * @param {truckParam} params
     */
        constructor(params = {}, paramInfo = []) {
          
        let tg = new T.SphereBufferGeometry(0.4);
        let tm = new T.MeshStandardMaterial();
        let target = new T.Mesh(tg,tm);
        target.visible = false;
  
        super(`Fountain-0`, target, paramInfo);
  
        // put the object in its place
        target.position.x = params.x;
        target.position.y = params.y;
        target.position.z = params.z;

        }
}

// beach ball 
let rainbow = new T.TextureLoader().load("../for_students/images/beachball.png");
let beachBallCtr = 0;
/**
 * @typedef beachBallParam
 * @type {object}
 * @property {number} [x=0]
 * @property {number} [y=0]
 * @property {number} [z=0]
 * @property {number} [scale=1]
 */
 export class beachBallGr extends GrObject {
    /**
     * @param {beachBallParam} params
     */
        constructor(params = {}, paramInfo = []) {
          
        let tg = new T.SphereBufferGeometry();
        let tm = new T.MeshStandardMaterial({
            color: "white",
            roughness: 0,
            map: rainbow
        });
        let target = new T.Mesh(tg,tm);
        super(`BeachBall-${beachBallCtr++}`, target, paramInfo);
  
        // put the object in its place
        target.position.x = params.x ? Number(params.x) : 0;
        target.position.y = params.y ? Number(params.y) : 1;
        target.position.z = params.z ? Number(params.z) : 0;
        
        let scale = params.scale ? Number(params.scale) : 1;
        target.scale.set(scale,scale,scale);

        this.ball = target;
        this.scale = scale;
        this.up = true;
        }
        stepWorld(delta){
            if(this.ball.position.y < this.scale) this.up = true;
            else if(this.ball.position.y > this.scale *3) this.up = false;

            if(this.up){ this.ball.translateY(0.005*delta);}
            else{ this.ball.translateY(-0.0025*delta);}
                    
            this.ball.rotateY(0.001*delta);
        }
}

// mirror
let mirrorCtr = 0;
/**
 * @typedef mirrorParam
 * @type {object}
 * @property {number} [x=0]
 * @property {number} [y=0]
 * @property {number} [z=0]
 * @property {number} [scale=1]
 * @property {number} [rotate=0]
 */
class mirror extends GrObject {
    /**
     * @param {mirrorParam} params
     */
    constructor(params = {}, paramInfo = []) {
        const cubeRenderTarget = new T.WebGLCubeRenderTarget(1024);

        let cc = new T.CubeCamera(0.1,1000, cubeRenderTarget);

        world.scene.add(cc);

        let mir_geo = new T.BoxBufferGeometry(2,3,0.25);

        let mir_mat = new T.MeshStandardMaterial({
            envMap: cubeRenderTarget.texture,
            roughness: 0.05,
		    metalness: 1
        });

        let mir_mesh = new T.Mesh(mir_geo,mir_mat);
        mir_mesh.translateZ(-5);
        mir_mesh.translateY(2);

        

        let frame = new T.Mesh(
          new T.BoxBufferGeometry(2.25,3.25,0.25),
          new T.MeshStandardMaterial({color: "goldenrod", roughness:0}));

        mir_mesh.add(frame);
        frame.translateZ(-0.025);
        
        super(`Mirror-${mirrorCtr++}`, mir_mesh, paramInfo);

        this.cc = cc;
        this.mir_mesh = mir_mesh;

        this.mir_mesh.position.x = params.x ? Number(params.x) : 0;
        this.mir_mesh.position.y = params.y ? Number(params.y) : 1.25;
        this.mir_mesh.position.z = params.z ? Number(params.z) : 0;
        mir_mesh.rotateY(params.rotate ? Number(params.rotate) : 0);
        let scale = params.scale ? Number(params.scale) : 1;
        mir_mesh.scale.set(scale,scale,scale);
        cc.position.copy(mir_mesh.position);

        cc.update(world.renderer,world.scene);
    }

    stepWorld(){
      this.cc.update(world.renderer,world.scene);
    }
  }



/**m
 * The Graphics Town Main -
 * This builds up the world and makes it go...
 */

// make the world
let world = new GrWorld({
    width: 800,
    height: 600,
    groundplane: false // make the ground plane big enough for a world of stuff
});

// Give the world a background
world.scene.background = new T.CubeTextureLoader()
.setPath( '../for_students/images/' )
.load( [
    'Right.png', 'Left.png',
    'Top.png', 'Front.png',
    'Back.png', 'Bottom.png'
]);

let sandGround = new groundGR({size:50});

// fountain 
const loader = new GLTFLoader();

loader.load(
	// resource URL
	'../for_students/fountain/scene.gltf',
	// called when the resource is loaded
	function ( gltf ) {
        gltf.scene.translateX(7);
		world.scene.add( gltf.scene );
	}
);

let fountainHelp = new fountainTargetGR({x:7,y:0.2,z:0});

// big trees
let p1 = new palmtreeGR({
    size: 2,
    x:-6,
});

let p2 = new palmtreeGR({
    size: 3,
    z:6,
});

let p3 = new palmtreeGR({
    size: 2.5,
    x:1.5,
    z:-1.5,
});

// snowmen
let s1 = new snowmanDuoGR({x:8,z:-5,scale:0.4});
let s2 = new snowmanDuoGR({x:10,z:-3,scale:0.4,counter:false});
let s3 = new snowmanDuoGR({x:12,z:-0,scale:0.4});
let s4 = new snowmanDuoGR({x:10,z:3,scale:0.4,counter:false});
let s5 = new snowmanDuoGR({x:8,z:5,scale:0.4});


// houses
let b1 = new beachHouseGR({
    scale: 4,
    x: 8,
    z: -11.5,});

let b2 = new beachHouseGR({
scale: 4,
x: 16,
z: -8,
rotate: -Math.PI/4});

let b3 = new beachHouseGR({
    scale: 4,
    x: 19,
    z: 0,
    rotate: Math.PI/2});

let b4 = new beachHouseGR({
scale: 4,
x: 16,
z: 8,
rotate: Math.PI/4});

let b5 = new beachHouseGR({
    scale: 4,
    x: 8,
    z: 11.5,
    rotate: Math.PI});

// house trees
let ph1 = new palmtreeGR({
    size: 2,
    x:12,
    z:-10
});
let ph2 = new palmtreeGR({
    size: 2.75,
    x:18,
    z:-4
});
let ph3 = new palmtreeGR({
    size: 2.25,
    x:18,
    z:4
});
let ph4 = new palmtreeGR({
    size: 2.5,
    x:12,
    z:10
});

// gulls
let bigTreePos = [p1.mesh.position, p2.mesh.position, 
    p3.mesh.position];

// stays by the big trees
let g1 = new seagullGR({y:10,x:-10, size:0.75,destination:bigTreePos});

let littleTreePos = [ph1.mesh.position, ph2.mesh.position, 
    ph3.mesh.position, ph4.mesh.position];

// stays by the little trees
let g2 = new seagullGR({y:2, x:6, destination:littleTreePos,size:0.5});
let g3 = new seagullGR({y:6, x:4, destination:littleTreePos,size:0.5});
let g4 = new seagullGR({y:4, x:2, destination:littleTreePos,size:0.5});

// goes to all trees
let g5 = new seagullGR({destination: bigTreePos.concat(littleTreePos)});

// trucks
let t1 = new truckGr({scale:2.5,x:4,z:-10, rotate:0.1});
let t2 = new truckGr({scale:2.5,x:1,z:-10, rotate:-0.15});
let t3 = new truckGr({scale:2.5,x:-2,z:-10, rotate: 0.1});
let t4 = new truckGr({scale:2.5,x:-5,z:-10});
let t5 = new truckGr({scale:2.5,x:-8,z:-10, rotate: Math.PI+0.1})

// beach ball
let bb1 = new beachBallGr({x:10,scale:0.5});

// mirror... more than 1 impacts performance dramatically
let m1 = new mirror({
    x:3, rotate:Math.PI/2, scale:0.75
});

world.add(b1);
world.add(b2);
world.add(b3);
world.add(b4);
world.add(b5);
world.add(s1);
world.add(s2);
world.add(s3);
world.add(s4);
world.add(s5);
world.add(g1);
world.add(g2);
world.add(g3);
world.add(g4);
world.add(g5);
world.add(sandGround);
world.add(p1);
world.add(p2);
world.add(p3);
world.add(ph1);
world.add(ph2);
world.add(ph3);
world.add(ph4);
world.add(t1);
world.add(t2);
world.add(t3);
world.add(t4);
world.add(t5);
world.add(fountainHelp);
world.add(bb1);
world.add(m1);

// put stuff into the world
// this calls the example code (that puts a lot of objects into the world)
// you can look at it for reference, but do not use it in your assignment
//main(world);

// while making your objects, be sure to identify some of them as "highlighted"

///////////////////////////////////////////////////////////////
// because I did not store the objects I want to highlight in variables, I need to look them up by name
// This code is included since it might be useful if you want to highlight your objects here
function highlight(obName) {
    const toHighlight = world.objects.find(ob => ob.name === obName);
    if (toHighlight) {
        toHighlight.highlighted = true;
    } else {
        throw `no object named ${obName} for highlighting!`;
    }
}
// of course, the student should highlight their own objects, not these
// highlight("SimpleHouse-5");
// highlight("Helicopter-0");
// highlight("Track Car");
// highlight("MorphTest");
highlight("PalmTree-0");
highlight("Seagull-4");
highlight("SnowmanDuo-0");
highlight("BeachHouse-0");
highlight("Truck-0");
highlight("Fountain-0");
highlight("BeachBall-0");
highlight("Mirror-0");

///////////////////////////////////////////////////////////////
// build and run the UI
// only after all the objects exist can we build the UI
// @ts-ignore       // we're sticking a new thing into the world
world.ui = new WorldUI(world);
// now make it go!
world.go();

