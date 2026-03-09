from gait_research_platform.data.sample_pose_dataset import generate_sample_pose_dataset


if __name__ == "__main__":
    generate_sample_pose_dataset("gait_research_platform/data/poses", num_videos=6, num_frames=64)
