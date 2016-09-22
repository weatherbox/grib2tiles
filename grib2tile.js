/*
 * @class Grib2tile
 * @author Yuta Tachibana
 *
 *
 */


function Grib2tile(url, tx, ty){
	this.url = url;
	this.tx = tx;
	this.ty = ty;

	return this;
}

Grib2tile.prototype.get = function(callback){
	var req = new XMLHttpRequest();
	req.open("GET", this.url, true);
	req.responseType = "arraybuffer";

	req.onload = function(){
		this._arraybuffer = req.response;
		this.parse(callback);
	};

	req.send(null);
	return;
};

Grib2tile.prototype.parse = function(callback){
	var dv = new DataView(this._arraybuffer);
	this._endian = false; // big endian

	// read meta data
	this.R = dv.getFloat32(0, this._endian);
	this.E = this.neg16(dv.getUint16(4, this._endian));
	this.D = this.neg16(dv.getUint16(6, this._endian)));

	// for reduce pow calls
	this._2E = Math.pow(2, this.E);
	this._10D = Math.pow(10, this.D);

	var offset = 8;
	var size = this.tx * this.ty;
	this.data = new Float32Array(size);
	var x1, x2, x3;

	// read each 2 datas (3byte)
	for (var i = 0; i < size / 2; i++){
		x1 = dv.getUint8(offset);
		x2 = dv.getUint8(offset + 1);
		x3 = dv.getUint8(offset + 2);

		this.data[2*i    ] = this.unpackSimple(x1 << 4 + x2 >> 4);
		this.data[2*i + 1] = this.unpackSimple((x2 & 0x0f) << 8 + x3);

		offset += 3;
	}

	// parse last one 
	if (size % 2 != 0){
		x1 = dv.getUint8(offset);
		x2 = dv.getUint8(offset + 1);

		this.data[2*(i + 1)] = this.unpackSimple(x1 << 4 + x2 >> 4);
	}

	return callback();
};


// first bit indicates negative number
Grib2tile.prototype.neg16 = function(x){
	if (x & 0x80 > 0) x = (x & 0x7f) * -1;
	return x;
};

// unpack simple packing
Grib2tile.prototype.unpackSimple = function(x){
	return (this.R + x * this._2E) / this._10D;
}

