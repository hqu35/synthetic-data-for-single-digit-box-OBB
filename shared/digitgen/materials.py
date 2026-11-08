"""Video-guide procedural plastic graph, with texture-driven printed ink."""
import bpy


def basic_material(name, color, roughness=.6, metallic=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    s = m.node_tree.nodes.get('Principled BSDF')
    s.inputs['Base Color'].default_value = (*color,1)
    s.inputs['Roughness'].default_value = roughness
    s.inputs['Metallic'].default_value = metallic
    s.inputs['IOR'].default_value = 1.5
    return m


def plastic(name, params, ink_image=None, preset=None):
    preset = preset or params['material_preset']
    dark = preset=='reference_dark_plastic'
    color = (.012,.014,.016) if dark else tuple(params['material_color'])
    m = basic_material(name,color)
    if preset=='basic':
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        base_output = None
        rough_output = None
    else:
        nodes, links = m.node_tree.nodes, m.node_tree.links
        def node(kind,name,x,y):
            n = nodes.new(kind); n.name = name; n.label = name; n.location = (x,y)
            return n
        bsdf = nodes.get('Principled BSDF'); bsdf.location = (700,160)
        tex = node('ShaderNodeTexCoord','Generated coordinates',-1000,0)
        mapping = node('ShaderNodeMapping','Shared Mapping',-800,0)
        links.new(tex.outputs['Generated'],mapping.inputs['Vector'])
        settings = [('Noise A',100,10,1,.1,'FBM',300),('Noise B',20,8,.9,.1,'FBM',0),('Noise C',30,10,1,2,'MULTIFRACTAL',-300)]
        for label,scale,detail,rough,distortion,fractal,y in settings:
            n = node('ShaderNodeTexNoise',label,-550,y)
            n.noise_dimensions = '3D'
            n.noise_type = fractal
            n.normalize = True
            for key,value in [('Scale',scale),('Detail',detail),('Roughness',rough),('Lacunarity',2),('Distortion',distortion)]:
                n.inputs[key].default_value = value
            links.new(mapping.outputs['Vector'],n.inputs['Vector'])
        ramp = node('ShaderNodeValToRGB','ColorRamp A',-230,380)
        if dark:
            colors = [(0.022,0.024,0.027,1),(.006,.007,.008,1)]
        else:
            aging,variation = params['aging_intensity'],params['color_variation']
            colors = [tuple(c*(1-variation)*(1-aging*.12) for c in color)+(1,), tuple(min(1,c*(1+variation)) for c in color)+(1,)]
        for stop,pos,col in zip(ramp.color_ramp.elements,[0,.5],colors):
            stop.position=pos;stop.color=col
        links.new(nodes['Noise A'].outputs['Fac'],ramp.inputs['Fac'])
        rough_ramp = node('ShaderNodeValToRGB','ColorRamp B',-230,180)
        output_range = (0,1) if dark else params.get('plastic_roughness',params['roughness_range'])
        for stop,pos,value in zip(rough_ramp.color_ramp.elements,[.3,.8],output_range):
            stop.position=pos;stop.color=(value,value,value,1)
        links.new(nodes['Noise A'].outputs['Fac'],rough_ramp.inputs['Fac'])
        multiply = node('ShaderNodeMath','Noise B x Noise C',-190,-130)
        multiply.operation = 'MULTIPLY'
        links.new(nodes['Noise B'].outputs['Fac'],multiply.inputs[0])
        links.new(nodes['Noise C'].outputs['Fac'],multiply.inputs[1])
        bump = node('ShaderNodeBump','Inverted micro bump',160,-130)
        bump.invert = True
        bump.inputs['Strength'].default_value = .05 if dark else params['micro_bump_strength']
        bump.inputs['Distance'].default_value = 1 if dark else params['micro_bump_distance']
        links.new(multiply.outputs[0],bump.inputs['Height'])
        links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
        base_output,rough_output = ramp.outputs['Color'],rough_ramp.outputs['Color']
        links.new(base_output,bsdf.inputs['Base Color'])
        links.new(rough_output,bsdf.inputs['Roughness'])
    if ink_image:
        nodes,links = m.node_tree.nodes,m.node_tree.links
        texture = nodes.new('ShaderNodeTexImage'); texture.name='Cylindrical ink mask'
        texture.image=ink_image;texture.extension='REPEAT';texture.interpolation='Linear'
        uv = nodes.new('ShaderNodeUVMap'); uv.uv_map='Circumference_Axial'
        links.new(uv.outputs['UV'],texture.inputs['Vector'])
        mix = nodes.new('ShaderNodeMixRGB'); mix.name='Ink / substrate color';mix.blend_type='MIX'
        links.new(texture.outputs['Color'],mix.inputs[0])
        if base_output: links.new(base_output,mix.inputs[1])
        else: mix.inputs[1].default_value=(*color,1)
        ink = (.82,.81,.76) if dark else tuple(params['ink_color'])
        mix.inputs[2].default_value=(*ink,1)
        links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        rough_mix=nodes.new('ShaderNodeMixRGB');rough_mix.name='Ink / substrate roughness'
        links.new(texture.outputs['Color'],rough_mix.inputs[0])
        if rough_output: links.new(rough_output,rough_mix.inputs[1])
        else: rough_mix.inputs[1].default_value=(.6,.6,.6,1)
        rough_mix.inputs[2].default_value=(params['ink_roughness'],)*3+(1,)
        if params.get('ink_gloss_enabled') is False and rough_output:
            links.new(rough_output,rough_mix.inputs[2])
        links.new(rough_mix.outputs[0],bsdf.inputs['Roughness'])
        if 'ink_gloss_enabled' in params:
            # Same nonmetallic Principled surface: the printed mask controls
            # roughness, normal microstructure, and supported specular IOR level.
            enabled=params['ink_gloss_enabled']
            if 'Specular IOR Level' in bsdf.inputs:
                spec=nodes.new('ShaderNodeMixRGB');spec.name='Ink / substrate specular IOR level'
                links.new(texture.outputs['Color'],spec.inputs[0])
                spec.inputs[1].default_value=(.5,.5,.5,1)
                value=params.get('ink_specular_ior_level',.5) if enabled else .5
                spec.inputs[2].default_value=(value,value,value,1)
                links.new(spec.outputs[0],bsdf.inputs['Specular IOR Level'])
                m['ink_specular_ior_level_supported']=True
            else:
                m['ink_specular_ior_level_supported']=False
            if 'Inverted micro bump' in nodes:
                bump=nodes['Inverted micro bump'];strength=params['micro_bump_strength']
                micro=nodes.new('ShaderNodeMixRGB');micro.name='Ink / substrate micro bump strength'
                links.new(texture.outputs['Color'],micro.inputs[0])
                micro.inputs[1].default_value=(strength,)*3+(1,)
                reduced=strength*params.get('ink_bump_scale',.1) if enabled else strength
                micro.inputs[2].default_value=(reduced,)*3+(1,)
                links.new(micro.outputs[0],bump.inputs['Strength'])
            m['ink_gloss_enabled']=enabled
    m['preset']=preset
    m['guide']='Plastic_Shader_操作指南.md; Noise A/B/C share Generated -> Mapping; Math Multiply -> inverted Bump'
    return m


def graph_report(material):
    nodes = material.node_tree.nodes
    return {'preset':material.get('preset'),'nodes':[
        {'name':n.name,'type':n.bl_idname,
         'noise_type':getattr(n,'noise_type',None), 'normalize':getattr(n,'normalize',None),
         'operation':getattr(n,'operation',None),
         'invert':getattr(n,'invert',None),
         'values':{s.name:s.default_value for s in n.inputs if s.type=='VALUE'},
         'ramp':[{'position':s.position,'color':list(s.color)} for s in n.color_ramp.elements] if hasattr(n,'color_ramp') else None}
        for n in nodes], 'links':[f'{l.from_node.name}.{l.from_socket.name} -> {l.to_node.name}.{l.to_socket.name}' for l in material.node_tree.links]}
