// This file was automatically generated from templates.soy.
// Please don't edit this file by hand.

if (typeof examples == 'undefined') { var examples = {}; }
if (typeof examples.simple == 'undefined') { examples.simple = {}; }


examples.simple.helloWorld = function(opt_data, opt_sb) {
  var output = opt_sb || new soy.StringBuilder();
  output.append('Hello world!');
  return opt_sb ? '' : output.toString();
};


examples.simple.destroy = function(opt_data, opt_sb) {
  var output = opt_sb || new soy.StringBuilder();
  output.append('Be destroyed!!!!!!!!!!');
  return opt_sb ? '' : output.toString();
};
