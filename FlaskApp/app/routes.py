from flask import Blueprint, request, jsonify
import os
import subprocess

# Create a Blueprint for the routes
film_routes = Blueprint('film_routes', __name__)

@film_routes.route('/api/interpolate', methods=['POST'])
def interpolate_video():
    """
    API to interpolate between static and generated videos.
    """
    try:
        # Get input data from the request
        data = request.json
        static_video_path = data.get('static_video_path')
        generated_video_path = data.get('generated_video_path')
        output_video_path = data.get('output_video_path')
        intermediate_gen2static = data.get('intermediate_gen2static')
        intermediate_static2gen = data.get('intermediate_static2gen')


        if not static_video_path or not generated_video_path:
            return jsonify({'error': 'Both static_video_path and generated_video_path are required'}), 400

        # Ensure intermediate frames directory exists
        os.makedirs(intermediate_gen2static, exist_ok=True)
        os.makedirs(intermediate_static2gen, exist_ok=True)
        os.makedirs("/home/ubuntu/output", exist_ok=True)

        # Extract the first and last frames of the static video
        static_first_frame = os.path.join(intermediate_gen2static, 'static_1.png')
        static_last_frame = os.path.join(intermediate_static2gen, 'end_static.png')
        subprocess.run([
            'ffmpeg', '-y', '-i', static_video_path, '-vf', "select=eq(n\\,0)", '-q:v', '3', static_first_frame
        ], check=True)
        subprocess.run([
            'ffmpeg', '-y', '-sseof', '-1', '-i', static_video_path, '-update', '1', '-q:v', '3', static_last_frame
        ], check=True)

        # Extract the first and last frames of the generated video
        generated_first_frame = os.path.join(intermediate_static2gen, 'generated_1.png')
        generated_last_frame = os.path.join(intermediate_gen2static, 'generated_2.png')
        subprocess.run([
            'ffmpeg', '-y', '-i', generated_video_path, '-vf', "select=eq(n\\,0)", '-q:v', '3', generated_first_frame
        ], check=True)
        subprocess.run([
            'ffmpeg', '-y', '-sseof', '-1', '-i', generated_video_path, '-update', '1', '-q:v', '3', generated_last_frame
        ], check=True)

        # # Prepare input pattern for interpolation
        # input_pattern = "gen2static"

        # Run the interpolation command
        subprocess.run([
            'python3', '-m', 'eval.interpolator_cli',
            '--pattern', "gen2static",
            '--model_path', '../pretrained_model/film_net/Style/saved_model',
            '--times_to_interpolate', '1',
            '--fps', '25',
            '--output_video'
        ], check=True)

        subprocess.run([
            'python3', '-m', 'eval.interpolator_cli',
            '--pattern', "static2gen",
            '--model_path', '../pretrained_model/film_net/Style/saved_model',
            '--times_to_interpolate', '1',
            '--fps', '25',
            '--output_video'
        ], check=True)

        # Return the path to the interpolated video

        subprocess.run([
            'ffmpeg', '-y', '-f' ,'concat', 
            '-safe', '0',
            '-i', 'videos.txt', 
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '/home/ubuntu/output/output.mp4'
        ])
        return jsonify({'message': 'Interpolation successful', 'output_video': output_video_path}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Command failed: {e}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500